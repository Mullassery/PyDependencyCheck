"""Tests for real health score computation and staleness detection."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from pydependencycheck.health import HealthAnalyzer, PackageStalenessChecker


class TestHealthAnalyzer:
    def test_perfect_project_scores_high(self):
        analyzer = HealthAnalyzer()
        deps = [{"name": "requests"}, {"name": "flask"}]
        score = analyzer.compute_health_score(
            dependencies=deps,
            vulnerabilities_by_pkg={},
            dead_deps=[],
            stale_packages=[],
        )
        assert score.score >= 90
        assert score.rating == "Excellent"
        assert score.issues == []

    def test_critical_vulnerability_tanks_score(self):
        analyzer = HealthAnalyzer()
        deps = [{"name": "requests"}]
        vulns = {"requests": [{"severity": "CRITICAL"}]}

        clean_score = analyzer.compute_health_score(deps, {}, [], [])
        vuln_score = analyzer.compute_health_score(deps, vulns, [], [])

        assert vuln_score.score < clean_score.score
        assert vuln_score.vulnerabilities_score < 100
        assert any("critical" in issue.lower() for issue in vuln_score.issues)

    def test_dead_dependencies_lower_quality_score(self):
        analyzer = HealthAnalyzer()
        deps = [{"name": f"pkg{i}"} for i in range(10)]

        score_clean = analyzer.compute_health_score(deps, {}, [], [])
        score_dead = analyzer.compute_health_score(deps, {}, ["pkg1", "pkg2", "pkg3", "pkg4"], [])

        assert score_dead.quality_score < score_clean.quality_score
        assert any("unused" in issue.lower() for issue in score_dead.issues)

    def test_stale_packages_lower_maintenance_score(self):
        analyzer = HealthAnalyzer()
        deps = [{"name": f"pkg{i}"} for i in range(4)]

        score = analyzer.compute_health_score(deps, {}, [], ["pkg1", "pkg2", "pkg3"])
        assert score.maintenance_score < 100

    def test_rating_thresholds(self):
        analyzer = HealthAnalyzer()
        assert analyzer._score_to_rating(95) == "Excellent"
        assert analyzer._score_to_rating(70) == "Good"
        assert analyzer._score_to_rating(55) == "Fair"
        assert analyzer._score_to_rating(40) == "Poor"
        assert analyzer._score_to_rating(10) == "Critical"

    def test_recommendation_lists_actual_dead_package_names(self):
        analyzer = HealthAnalyzer()
        deps = [{"name": "a"}, {"name": "b"}]
        score = analyzer.compute_health_score(deps, {}, ["unused-pkg"], [])
        assert any("unused-pkg" in rec for rec in score.recommendations)

    def test_empty_project_has_no_issues(self):
        analyzer = HealthAnalyzer()
        score = analyzer.compute_health_score([], {}, [], [])
        # complexity_score caps at 95 (not 100) even for a trivially small
        # dependency set, so the weighted total lands at 99, not 100.
        assert score.score >= 95
        assert score.rating == "Excellent"
        assert score.issues == []


def _pypi_release_response(days_old):
    upload_time = (datetime.now(timezone.utc) - timedelta(days=days_old)).strftime("%Y-%m-%dT%H:%M:%S")
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "releases": {
            "1.0.0": [{"upload_time_iso_8601": upload_time + "Z"}],
        }
    }
    return response


class TestPackageStalenessChecker:
    def test_recent_release_is_not_stale(self):
        checker = PackageStalenessChecker()
        with patch("pydependencycheck.health.requests.get") as mock_get:
            mock_get.return_value = _pypi_release_response(days_old=30)
            assert checker.is_stale("fresh-package") is False

    def test_old_release_is_stale(self):
        checker = PackageStalenessChecker()
        with patch("pydependencycheck.health.requests.get") as mock_get:
            mock_get.return_value = _pypi_release_response(days_old=800)
            assert checker.is_stale("ancient-package") is True

    def test_unknown_package_is_not_flagged_stale(self):
        """A network failure means we don't *know* the package is stale --
        it must not be silently counted against the health score."""
        checker = PackageStalenessChecker()
        with patch("pydependencycheck.health.requests.get", side_effect=ConnectionError("boom")):
            assert checker.is_stale("unreachable-package") is False

    def test_find_stale_packages_filters_correctly(self):
        checker = PackageStalenessChecker()
        deps = [{"name": "old-pkg"}, {"name": "new-pkg"}]

        def fake_get(url, timeout=5.0):
            if "old-pkg" in url:
                return _pypi_release_response(days_old=900)
            return _pypi_release_response(days_old=10)

        with patch("pydependencycheck.health.requests.get", side_effect=fake_get):
            stale = checker.find_stale_packages(deps)

        assert stale == ["old-pkg"]

    def test_custom_threshold_respected(self):
        checker = PackageStalenessChecker()
        with patch("pydependencycheck.health.requests.get") as mock_get:
            mock_get.return_value = _pypi_release_response(days_old=100)
            assert checker.is_stale("pkg", days_threshold=365) is False
            assert checker.is_stale("pkg", days_threshold=30) is True


class TestAdditionalHealthCases:
    def test_health_score_defaults_are_independent(self):
        from pydependencycheck.health import HealthScore

        first = HealthScore(1, "Critical", 1, 1, 1, 1)
        second = HealthScore(2, "Poor", 2, 2, 2, 2)
        first.issues.append("x")
        assert second.issues == []

    def test_complexity_buckets(self):
        analyzer = HealthAnalyzer()
        assert analyzer._score_complexity(101, None) == 40
        assert analyzer._score_complexity(51, None) == 60
        assert analyzer._score_complexity(21, None) == 80
        assert analyzer._score_complexity(20, None) == 95

    def test_combined_penalties_and_recommendations(self):
        analyzer = HealthAnalyzer()
        deps = [{"name": f"pkg-{i}"} for i in range(10)]
        vulns = {"pkg-0": [{"severity": "CRITICAL"}], "pkg-1": [{"severity": "HIGH"}]}
        score = analyzer.compute_health_score(
            deps,
            vulns,
            dead_deps=["pkg-2", "pkg-3"],
            stale_packages=["pkg-4", "pkg-5", "pkg-6"],
        )
        assert score.vulnerabilities_score == 70
        assert score.quality_score == 60
        assert score.maintenance_score == 50
        assert any("Upgrade pkg-0" in rec for rec in score.recommendations)
        assert any("3 stale" in rec for rec in score.recommendations)


class TestAdditionalStalenessCases:
    def test_latest_release_wins_over_older_releases(self, monkeypatch):
        checker = PackageStalenessChecker()
        old = (datetime.now(timezone.utc) - timedelta(days=900)).isoformat()
        recent = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        monkeypatch.setattr(
            "pydependencycheck.health.requests.get",
            lambda *a, **k: _pypi_release_response_payload(old, recent),
        )
        assert checker.is_stale("demo") is False

    def test_malformed_timestamps_are_ignored(self, monkeypatch):
        checker = PackageStalenessChecker()
        monkeypatch.setattr(
            "pydependencycheck.health.requests.get",
            lambda *a, **k: _pypi_release_response_payload("not-a-date"),
        )
        assert checker.last_release_date("demo") is None
        assert checker.is_stale("demo") is False


class _PayloadResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def _pypi_release_response_payload(*upload_times):
    return _PayloadResponse(
        {"releases": {f"1.0.{index}": [{"upload_time_iso_8601": value}] for index, value in enumerate(upload_times)}}
    )
