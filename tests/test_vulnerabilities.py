"""Tests for the pure-Python OSV fallback client."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
import requests
from pydependencycheck.vulnerabilities import (
    Vulnerability,
    VulnerabilityAnalyzer,
    VulnerabilityReport,
)


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_report_defaults_are_independent() -> None:
    first = VulnerabilityReport(package="a", version=None)
    second = VulnerabilityReport(package="b", version=None)
    first.vulnerabilities.append(Vulnerability("X", "s", "LOW"))
    assert second.vulnerabilities == []
    assert first.risk_score == 0
    assert first.rating == "unknown"


def test_query_and_risk_scoring(monkeypatch: pytest.MonkeyPatch) -> None:
    analyzer = VulnerabilityAnalyzer()
    payload = {
        "vulns": [
            {
                "id": "CVE-1",
                "summary": "critical issue",
                "cvss_v3_score": 9.8,
                "affected": ["<2.0"],
                "fixed_version": "2.0",
                "published": "2026-01-01",
                "references": [{"url": "https://example.com/CVE-1"}],
            },
            {
                "id": "CVE-2",
                "summary": "explicit severity",
                "severity": "high",
            },
        ]
    }
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return _Response(payload)

    monkeypatch.setattr(analyzer.session, "post", fake_post)

    report = analyzer.analyze_package("requests", "2.32.0")

    assert calls[0][1]["version"] == "2.32.0"
    assert [v.id for v in report.vulnerabilities] == ["CVE-1", "CVE-2"]
    assert report.vulnerabilities[0].severity == "CRITICAL"
    assert report.vulnerabilities[1].severity == "HIGH"
    assert report.vulnerabilities[0].references == ["https://example.com/CVE-1"]
    assert report.risk_score == 86
    assert report.rating == "Critical"


def test_cache_avoids_second_network_call(monkeypatch: pytest.MonkeyPatch) -> None:
    analyzer = VulnerabilityAnalyzer()
    calls = 0

    def fake_post(url, json, timeout):
        nonlocal calls
        calls += 1
        return _Response({"vulns": []})

    monkeypatch.setattr(analyzer.session, "post", fake_post)

    assert analyzer.analyze_package("requests", "2.32.0").vulnerabilities == []
    assert analyzer.analyze_package("requests", "2.32.0").vulnerabilities == []
    assert calls == 1


def test_expired_cache_is_refetched(monkeypatch: pytest.MonkeyPatch) -> None:
    analyzer = VulnerabilityAnalyzer()
    calls = 0

    def fake_post(url, json, timeout):
        nonlocal calls
        calls += 1
        return _Response({"vulns": []})

    monkeypatch.setattr(analyzer.session, "post", fake_post)
    analyzer.analyze_package("requests", "2.32.0")
    key = "requests@2.32.0"
    vulns, _ = analyzer.cache[key]
    analyzer.cache[key] = (vulns, datetime.now() - timedelta(seconds=analyzer.CACHE_TTL + 1))

    analyzer.analyze_package("requests", "2.32.0")
    assert calls == 2


def test_network_error_degrades_to_empty_report(monkeypatch: pytest.MonkeyPatch) -> None:
    analyzer = VulnerabilityAnalyzer()

    def fake_post(url, json, timeout):
        raise requests.RequestException("offline")

    monkeypatch.setattr(analyzer.session, "post", fake_post)
    report = analyzer.analyze_package("requests")

    assert report.vulnerabilities == []
    assert report.risk_score == 0
    assert report.rating == "Minimal"


def test_analyze_project_counts_by_severity(monkeypatch: pytest.MonkeyPatch) -> None:
    analyzer = VulnerabilityAnalyzer()

    def fake_analyze(package, version=None):
        return VulnerabilityReport(
            package=package,
            version=version,
            vulnerabilities=[
                Vulnerability("A", "critical", "CRITICAL", cvss_score=9.5),
                Vulnerability("B", "high", "HIGH"),
                Vulnerability("C", "medium", "MEDIUM"),
                Vulnerability("D", "low", "LOW"),
            ],
            risk_score=70,
            rating="High",
        )

    monkeypatch.setattr(analyzer, "analyze_package", fake_analyze)
    result = analyzer.analyze_project([{"name": "one", "version": "1.0"}, {"name": "two", "version": "2.0"}])

    assert result["total_packages"] == 2
    assert result["packages_with_vulns"] == 2
    assert result["total_vulns"] == 8
    assert result["critical"] == 2
    assert result["high"] == 2
    assert result["medium"] == 2
    assert result["low"] == 2
    assert result["packages"][0]["rating"] == "High"


def test_score_to_rating_boundaries() -> None:
    analyzer = VulnerabilityAnalyzer()
    assert analyzer._score_to_rating(80) == "Critical"
    assert analyzer._score_to_rating(60) == "High"
    assert analyzer._score_to_rating(40) == "Medium"
    assert analyzer._score_to_rating(20) == "Low"
    assert analyzer._score_to_rating(0) == "Minimal"
