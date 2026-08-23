"""GitHub Actions integration for CI/CD"""

import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class GitHubActionsReporter:
    """Report findings as GitHub Actions annotations"""

    def __init__(self):
        self.in_ci = "GITHUB_ACTIONS" in os.environ
        self.workflow_name = os.getenv("GITHUB_WORKFLOW", "Unknown")
        self.run_id = os.getenv("GITHUB_RUN_ID", "0")

    def report_vulnerabilities(self, vulnerabilities: Dict[str, List[Dict]]) -> None:
        """Report vulnerabilities as GitHub Actions warnings"""
        if not self.in_ci:
            return

        for package, vulns in vulnerabilities.items():
            for vuln in vulns:
                severity = vuln.get("severity", "MEDIUM").upper()
                level = "error" if severity in ("CRITICAL", "HIGH") else "warning"

                msg = f"Package '{package}' has {severity} vulnerability: {vuln.get('summary', 'N/A')}"

                if vuln.get("fixed_version"):
                    msg += f" (fix available in {vuln['fixed_version']})"

                self._output_annotation(level, msg, file="requirements.txt")

    def report_dead_dependencies(self, dead_deps: List[str]) -> None:
        """Report unused dependencies"""
        if not self.in_ci or not dead_deps:
            return

        msg = f"Found {len(dead_deps)} potentially unused dependencies: {', '.join(dead_deps[:5])}"
        if len(dead_deps) > 5:
            msg += f" and {len(dead_deps) - 5} more"

        self._output_annotation("notice", msg, file="requirements.txt")

    def report_health_score(self, health_score: int, issues: List[str]) -> None:
        """Report health score and issues"""
        if not self.in_ci:
            return

        rating = self._score_to_rating(health_score)
        msg = f"Dependency health score: {health_score}/100 ({rating})"

        level = "error" if health_score < 40 else "warning" if health_score < 65 else "notice"

        self._output_annotation(level, msg)

        for issue in issues[:3]:  # Report top 3 issues
            self._output_annotation("warning", issue)

    def report_drift(self, drift: Dict[str, Any]) -> None:
        """Report dependency drift"""
        if not self.in_ci or not drift.get("changed"):
            return

        changes = []
        if drift.get("added"):
            changes.append(f"Added: {len(drift['added'])} packages")
        if drift.get("removed"):
            changes.append(f"Removed: {len(drift['removed'])} packages")
        if drift.get("upgraded"):
            changes.append(f"Upgraded: {len(drift['upgraded'])} packages")
        if drift.get("downgraded"):
            changes.append(f"Downgraded: {len(drift['downgraded'])} packages")

        msg = "Dependency drift detected: " + ", ".join(changes)
        self._output_annotation("warning", msg)

    def fail_if_criteria_met(
        self,
        health_score: int,
        critical_vulns: int,
        dead_deps_threshold: int,
        dead_deps_count: int,
    ) -> bool:
        """Check if CI should fail based on criteria"""
        should_fail = False

        if critical_vulns > 0:
            self._output_annotation("error", f"CI failing: {critical_vulns} critical vulnerabilities detected")
            should_fail = True

        if health_score < 50:
            self._output_annotation("error", f"CI failing: Health score {health_score}/100 below threshold of 50")
            should_fail = True

        if dead_deps_count > dead_deps_threshold:
            self._output_annotation(
                "error", f"CI failing: {dead_deps_count} unused deps exceed threshold of {dead_deps_threshold}"
            )
            should_fail = True

        return should_fail

    @staticmethod
    def _output_annotation(level: str, message: str, file: str = "pyproject.toml") -> None:
        """Output GitHub Actions annotation"""
        # Use GitHub Actions workflow command syntax
        # ::notice::message
        # ::warning::message
        # ::error::message

        print(f"::{level} file={file}::{message}")

    @staticmethod
    def _score_to_rating(score: int) -> str:
        """Convert score to rating"""
        if score >= 80:
            return "Excellent"
        elif score >= 65:
            return "Good"
        elif score >= 50:
            return "Fair"
        else:
            return "Poor"


def create_github_actions_workflow() -> str:
    """Generate GitHub Actions workflow YAML"""
    workflow = """name: Dependency Check

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 9 * * MON'  # Weekly on Monday

jobs:
  dependency-check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install PyDependencyCheck
        run: pip install pydependencycheck

      - name: Scan dependencies
        run: |
          pydependencycheck scan . --save-snapshot

      - name: Check for vulnerabilities
        run: |
          pydependencycheck health

      - name: Detect drift
        run: |
          pydependencycheck drift --baseline main
        continue-on-error: true

      - name: Generate SBOM
        run: |
          pydependencycheck export --format cyclonedx --output sbom.json
        continue-on-error: true

      - name: Upload SBOM
        uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: sbom.json
        if: always()
"""
    return workflow
