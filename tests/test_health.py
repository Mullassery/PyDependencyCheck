"""Health scoring and PyPI staleness checks."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import requests
from pydependencycheck.health import (
    HealthAnalyzer,
    HealthScore,
    PackageStalenessChecker,
)


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def _pypi_payload(*upload_times: str) -> dict:
    return {"releases": {f"1.0.{index}": [{"upload_time_iso_8601": value}] for index, value in enumerate(upload_times)}}


def test_health_score_defaults_are_independent() -> None:
    first = HealthScore(1, "Critical", 1, 1, 1, 1)
    second = HealthScore(2, "Poor", 2, 2, 2, 2)
    first.issues.append("x")
    assert second.issues == []


def test_compute_health_score_for_clean_project() -> None:
    score = HealthAnalyzer().compute_health_score([], {}, [], [])
    assert score.score == 99
    assert score.rating == "Excellent"
    assert score.vulnerabilities_score == 100
    assert score.quality_score == 100
    assert score.issues == []
    assert score.recommendations == []


def test_compute_health_score_penalizes_critical_vulns_and_dead_deps() -> None:
    deps = [{"name": f"pkg-{i}"} for i in range(10)]
    vulns = {
        "pkg-0": [{"severity": "CRITICAL"}],
        "pkg-1": [{"severity": "HIGH"}],
    }
    score = HealthAnalyzer().compute_health_score(
        deps,
        vulns,
        dead_deps=["pkg-2", "pkg-3"],
        stale_packages=["pkg-4", "pkg-5", "pkg-6"],
    )
    assert score.vulnerabilities_score == 70
    assert score.quality_score == 60
    assert score.maintenance_score == 50
    assert score.rating in {"Fair", "Poor"}
    assert any("critical" in issue for issue in score.issues)
    assert any("unused" in issue for issue in score.issues)
    assert any("Upgrade pkg-0" in rec for rec in score.recommendations)
    assert any("3 stale" in rec for rec in score.recommendations)


def test_complexity_buckets_and_rating_boundaries() -> None:
    analyzer = HealthAnalyzer()
    assert analyzer._score_complexity(101, None) == 40
    assert analyzer._score_complexity(51, None) == 60
    assert analyzer._score_complexity(21, None) == 80
    assert analyzer._score_complexity(20, None) == 95
    assert analyzer._score_to_rating(80) == "Excellent"
    assert analyzer._score_to_rating(65) == "Good"
    assert analyzer._score_to_rating(50) == "Fair"
    assert analyzer._score_to_rating(35) == "Poor"
    assert analyzer._score_to_rating(34) == "Critical"


def test_staleness_uses_latest_release(monkeypatch: pytest.MonkeyPatch) -> None:
    checker = PackageStalenessChecker()
    old = (datetime.now(timezone.utc) - timedelta(days=900)).isoformat()
    recent = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    monkeypatch.setattr(
        "pydependencycheck.health.requests.get",
        lambda *a, **k: _Response(_pypi_payload(old, recent)),
    )
    assert checker.last_release_date("demo") is not None
    assert checker.is_stale("demo") is False


def test_staleness_flags_old_package(monkeypatch: pytest.MonkeyPatch) -> None:
    checker = PackageStalenessChecker()
    old = (datetime.now(timezone.utc) - timedelta(days=900)).isoformat()
    monkeypatch.setattr(
        "pydependencycheck.health.requests.get",
        lambda *a, **k: _Response(_pypi_payload(old)),
    )
    assert checker.is_stale("demo") is True
    assert checker.find_stale_packages([{"name": "demo"}, {}]) == ["demo"]


def test_staleness_network_failure_is_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    checker = PackageStalenessChecker()

    def boom(*args, **kwargs):
        raise requests.RequestException("offline")

    monkeypatch.setattr("pydependencycheck.health.requests.get", boom)
    assert checker.last_release_date("demo") is None
    assert checker.is_stale("demo") is False


def test_staleness_ignores_malformed_timestamps(monkeypatch: pytest.MonkeyPatch) -> None:
    checker = PackageStalenessChecker()
    monkeypatch.setattr(
        "pydependencycheck.health.requests.get",
        lambda *a, **k: _Response({"releases": {"1.0": [{"upload_time": "not-a-date"}]}}),
    )
    assert checker.last_release_date("demo") is None
