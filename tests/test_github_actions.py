"""Tests for GitHub Actions CI gating and annotation output."""

import pytest

from pydependencycheck.github_actions import GitHubActionsReporter, create_github_actions_workflow


@pytest.fixture
def in_ci(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_WORKFLOW", "Dependency Check")
    monkeypatch.setenv("GITHUB_RUN_ID", "12345")


@pytest.fixture
def not_in_ci(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)


class TestGitHubActionsReporterAnnotations:
    def test_detects_ci_environment(self, in_ci):
        reporter = GitHubActionsReporter()
        assert reporter.in_ci is True

    def test_detects_non_ci_environment(self, not_in_ci):
        reporter = GitHubActionsReporter()
        assert reporter.in_ci is False

    def test_vulnerability_annotation_uses_error_for_critical(self, in_ci, capsys):
        reporter = GitHubActionsReporter()
        reporter.report_vulnerabilities(
            {"requests": [{"severity": "CRITICAL", "summary": "RCE vulnerability", "fixed_version": "2.32.1"}]}
        )
        out = capsys.readouterr().out
        assert "::error" in out
        assert "requests" in out
        assert "2.32.1" in out

    def test_vulnerability_annotation_uses_warning_for_medium(self, in_ci, capsys):
        reporter = GitHubActionsReporter()
        reporter.report_vulnerabilities({"flask": [{"severity": "MEDIUM", "summary": "minor issue"}]})
        out = capsys.readouterr().out
        assert "::warning" in out
        assert "::error" not in out

    def test_no_annotations_outside_ci(self, not_in_ci, capsys):
        reporter = GitHubActionsReporter()
        reporter.report_vulnerabilities({"requests": [{"severity": "CRITICAL", "summary": "x"}]})
        out = capsys.readouterr().out
        assert out == ""

    def test_dead_dependencies_annotation(self, in_ci, capsys):
        reporter = GitHubActionsReporter()
        reporter.report_dead_dependencies(["unused1", "unused2"])
        out = capsys.readouterr().out
        assert "::notice" in out
        assert "unused1" in out

    def test_no_dead_dependencies_annotation_when_empty(self, in_ci, capsys):
        reporter = GitHubActionsReporter()
        reporter.report_dead_dependencies([])
        out = capsys.readouterr().out
        assert out == ""

    def test_health_score_annotation_severity(self, in_ci, capsys):
        reporter = GitHubActionsReporter()
        reporter.report_health_score(30, ["critical issue"])
        out = capsys.readouterr().out
        assert "::error" in out
        assert "30/100" in out

    def test_drift_annotation(self, in_ci, capsys):
        reporter = GitHubActionsReporter()
        reporter.report_drift({"changed": True, "added": ["a"], "removed": [], "upgraded": [], "downgraded": []})
        out = capsys.readouterr().out
        assert "::warning" in out
        assert "Added: 1 packages" in out

    def test_no_drift_annotation_when_unchanged(self, in_ci, capsys):
        reporter = GitHubActionsReporter()
        reporter.report_drift({"changed": False})
        out = capsys.readouterr().out
        assert out == ""


class TestGateExitCriteria:
    def test_fails_on_critical_vulnerabilities(self):
        reporter = GitHubActionsReporter()
        should_fail = reporter.fail_if_criteria_met(
            health_score=90, critical_vulns=1, dead_deps_threshold=10, dead_deps_count=0
        )
        assert should_fail is True

    def test_fails_on_low_health_score(self):
        reporter = GitHubActionsReporter()
        should_fail = reporter.fail_if_criteria_met(
            health_score=30, critical_vulns=0, dead_deps_threshold=10, dead_deps_count=0
        )
        assert should_fail is True

    def test_fails_when_dead_deps_exceed_threshold(self):
        reporter = GitHubActionsReporter()
        should_fail = reporter.fail_if_criteria_met(
            health_score=90, critical_vulns=0, dead_deps_threshold=5, dead_deps_count=6
        )
        assert should_fail is True

    def test_passes_clean_project(self):
        reporter = GitHubActionsReporter()
        should_fail = reporter.fail_if_criteria_met(
            health_score=90, critical_vulns=0, dead_deps_threshold=10, dead_deps_count=2
        )
        assert should_fail is False


class TestScoreToRating:
    def test_rating_boundaries(self):
        assert GitHubActionsReporter._score_to_rating(85) == "Excellent"
        assert GitHubActionsReporter._score_to_rating(70) == "Good"
        assert GitHubActionsReporter._score_to_rating(55) == "Fair"
        assert GitHubActionsReporter._score_to_rating(20) == "Poor"


class TestWorkflowGeneration:
    def test_generated_workflow_is_valid_yaml(self):
        yaml = pytest.importorskip("yaml")
        workflow = create_github_actions_workflow()
        parsed = yaml.safe_load(workflow)
        assert "jobs" in parsed
        assert "dependency-check" in parsed["jobs"]

    def test_generated_workflow_references_real_commands(self):
        workflow = create_github_actions_workflow()
        assert "pydependencycheck scan" in workflow
        assert "pydependencycheck health" in workflow
