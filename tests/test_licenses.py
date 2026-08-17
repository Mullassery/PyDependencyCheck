"""Tests for license detection and compliance checking (network mocked)."""

from unittest.mock import MagicMock, patch

from pydependencycheck.licenses import (
    DeadDependencyDetector,
    LicenseAnalyzer,
    LicenseInfo,
)


def _mock_pypi_response(license_field=None, classifiers=None, version="1.0.0"):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "info": {
            "license": license_field,
            "classifiers": classifiers or [],
            "version": version,
        }
    }
    return response


class TestLicenseAnalyzerClassification:
    def test_mit_classifier_is_permissive(self):
        analyzer = LicenseAnalyzer()
        with patch("pydependencycheck.licenses.requests.get") as mock_get:
            mock_get.return_value = _mock_pypi_response(classifiers=["License :: OSI Approved :: MIT License"])
            info = analyzer.analyze_package("some-mit-package")

        assert info.risk_level == "permissive"
        assert "MIT License" in info.licenses

    def test_gpl_is_restricted(self):
        analyzer = LicenseAnalyzer()
        with patch("pydependencycheck.licenses.requests.get") as mock_get:
            mock_get.return_value = _mock_pypi_response(license_field="GPL-3.0")
            info = analyzer.analyze_package("some-gpl-package")

        assert info.risk_level == "restricted"

    def test_lgpl_is_copyleft_not_restricted(self):
        analyzer = LicenseAnalyzer()
        with patch("pydependencycheck.licenses.requests.get") as mock_get:
            mock_get.return_value = _mock_pypi_response(license_field="LGPL-2.1")
            info = analyzer.analyze_package("some-lgpl-package")

        assert info.risk_level == "copyleft"

    def test_no_license_data_is_unknown(self):
        analyzer = LicenseAnalyzer()
        with patch("pydependencycheck.licenses.requests.get") as mock_get:
            mock_get.return_value = _mock_pypi_response(license_field=None, classifiers=[])
            info = analyzer.analyze_package("some-unlicensed-package")

        assert info.risk_level == "unknown"

    def test_network_failure_degrades_to_unknown_not_crash(self):
        analyzer = LicenseAnalyzer()
        with patch("pydependencycheck.licenses.requests.get", side_effect=ConnectionError("boom")):
            info = analyzer.analyze_package("some-package")

        assert info.risk_level == "unknown"
        assert info.package == "some-package"

    def test_results_are_cached(self):
        analyzer = LicenseAnalyzer(cache_licenses=True)
        with patch("pydependencycheck.licenses.requests.get") as mock_get:
            mock_get.return_value = _mock_pypi_response(license_field="MIT")
            analyzer.analyze_package("cached-package")
            analyzer.analyze_package("cached-package")

        assert mock_get.call_count == 1


class TestLicenseCompatibility:
    def test_mit_dependency_always_compatible(self):
        analyzer = LicenseAnalyzer()
        compatible, conflicts = analyzer.check_compatibility("Apache-2.0", ["MIT"])
        assert compatible is True
        assert conflicts == []

    def test_gpl_conflicts_with_permissive_project(self):
        analyzer = LicenseAnalyzer()
        compatible, conflicts = analyzer.check_compatibility("Apache-2.0", ["GPL-3.0"])
        assert compatible is False
        assert len(conflicts) == 1

    def test_mismatched_copyleft_versions_conflict(self):
        analyzer = LicenseAnalyzer()
        compatible, conflicts = analyzer.check_compatibility("GPL-2.0", ["GPL-3.0"])
        assert compatible is False


class TestAnalyzeProjectLicenses:
    def test_aggregates_risk_counts(self):
        analyzer = LicenseAnalyzer()
        deps = [{"name": "pkg-a", "version": "1.0"}, {"name": "pkg-b", "version": "2.0"}]

        responses = [
            _mock_pypi_response(license_field="MIT"),
            _mock_pypi_response(license_field="GPL-3.0"),
        ]
        with patch("pydependencycheck.licenses.requests.get", side_effect=responses):
            report = analyzer.analyze_project_licenses(deps)

        assert report["total"] == 2
        assert report["permissive"] == 1
        assert report["restricted"] == 1
        assert len(report["packages"]) == 2


class TestLicenseInfo:
    def test_str_representation(self):
        info = LicenseInfo(package="foo", licenses=["MIT"], risk_level="permissive")
        assert str(info) == "foo: MIT (permissive)"

    def test_str_with_no_licenses(self):
        info = LicenseInfo(package="foo")
        assert "Unknown" in str(info)


class TestDeadDependencyDetector:
    def test_finds_unused_declared_packages(self):
        detector = DeadDependencyDetector()
        result = detector.find_dead_dependencies(
            declared=["requests", "flask", "unused-pkg"], used=["requests", "flask"]
        )

        assert result["definitely_dead"] == ["unused-pkg"]
        assert len(result["recommendations"]) == 1

    def test_no_dead_dependencies_when_all_used(self):
        detector = DeadDependencyDetector()
        result = detector.find_dead_dependencies(declared=["requests"], used=["requests"])

        assert result["definitely_dead"] == []
        assert result["recommendations"] == []

    def test_normalizes_underscores_and_case(self):
        detector = DeadDependencyDetector()
        result = detector.find_dead_dependencies(declared=["My_Package"], used=["my-package"])
        assert result["definitely_dead"] == []
