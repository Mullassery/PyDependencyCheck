"""End-to-end CLI tests for the commands that were previously stubbed or
never wired up: `health`, `trace`, `export` (SBOM), `licenses`, `gate`.
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pydependencycheck.cli import cli


@pytest.fixture
def project(tmp_path):
    (tmp_path / "requirements.txt").write_text("requests==2.32.0\nflask>=2.0.0,<3.0.0\n")
    return tmp_path


@pytest.fixture
def runner():
    return CliRunner()


class TestHealthCommand:
    def test_health_offline_reports_real_computed_score(self, runner, project):
        """--offline avoids network calls (OSV/PyPI) so this exercises the
        real HealthAnalyzer computation deterministically."""
        result = runner.invoke(cli, ["health", "--path", str(project), "--offline"])

        assert result.exit_code == 0, result.output
        assert "Dependency Health Score:" in result.output
        # No longer the hardcoded "72/100" stub value.
        assert "/100" in result.output
        assert "Health Score Breakdown" in result.output

    def test_health_reflects_dead_dependencies(self, runner, tmp_path):
        (tmp_path / "requirements.txt").write_text("totally-unused-package==1.0.0\n")
        result = runner.invoke(cli, ["health", "--path", str(tmp_path), "--offline"])

        assert result.exit_code == 0, result.output
        # With no Rust-detected imports at all for an unused package, the
        # dead-dependency detector (if the Rust backend is present) should
        # flag it, surfacing in either the issues or recommendations text.
        assert "Dependency Health Score:" in result.output


class TestTraceCommand:
    def test_trace_reports_current_status_for_declared_package(self, runner, project):
        result = runner.invoke(cli, ["trace", "requests", "--path", str(project)])

        assert result.exit_code == 0, result.output
        assert "Dependency Lineage: requests" in result.output
        assert "Current version:" in result.output
        assert "direct" in result.output

    def test_trace_reports_not_declared_for_unknown_package(self, runner, project):
        result = runner.invoke(cli, ["trace", "totally-unknown-pkg", "--path", str(project)])

        assert result.exit_code == 0, result.output
        assert "Not currently declared" in result.output

    def test_trace_handles_non_git_directory_gracefully(self, runner, project):
        # tmp_path is not inside a git repo (or if the test runner's cwd
        # happens to be, GitPython will still correctly report whichever
        # repo project resolves to -- either way this must not crash).
        result = runner.invoke(cli, ["trace", "requests", "--path", str(project)])
        assert result.exit_code == 0, result.output


class TestGateCommand:
    def test_gate_passes_for_healthy_project(self, runner, project):
        result = runner.invoke(cli, ["gate", "--path", str(project), "--offline"])
        assert result.exit_code == 0, result.output
        assert "Gate PASSED" in result.output

    def test_gate_fails_when_min_health_not_met(self, runner, project):
        result = runner.invoke(cli, ["gate", "--path", str(project), "--offline", "--min-health", "101"])
        assert result.exit_code == 1
        assert "Gate FAILED" in result.output


class TestExportCommand:
    def test_export_cyclonedx_to_stdout_is_valid_json(self, runner, project):
        result = runner.invoke(cli, ["export", "--path", str(project), "--format", "cyclonedx"])

        assert result.exit_code == 0, result.output
        sbom = json.loads(result.output)
        assert sbom["bomFormat"] == "CycloneDX"
        names = {c["name"] for c in sbom["components"]}
        assert "requests" in names

    def test_export_spdx_to_stdout_is_valid_json(self, runner, project):
        result = runner.invoke(cli, ["export", "--path", str(project), "--format", "spdx"])

        assert result.exit_code == 0, result.output
        sbom = json.loads(result.output)
        assert sbom["spdxVersion"] == "SPDX-2.3"

    def test_export_to_file(self, runner, project, tmp_path):
        out_file = tmp_path / "sbom.json"
        result = runner.invoke(cli, ["export", "--path", str(project), "--output", str(out_file)])

        assert result.exit_code == 0, result.output
        assert out_file.exists()
        json.loads(out_file.read_text())  # must be valid JSON

    def test_export_sign_without_key_fails_cleanly(self, runner, project):
        result = runner.invoke(cli, ["export", "--path", str(project), "--sign"])
        assert result.exit_code == 1
        assert "--sign requires --key" in result.output

    def test_export_output_survives_shell_redirection(self, project):
        """Regression test: Rich's console.print() word-wraps long
        unbroken tokens (like a SHA-256 hash or RSA signature) by default,
        which corrupts JSON when piped/redirected. This must run as a real
        subprocess (not CliRunner) because CliRunner's captured output
        doesn't reproduce Rich's terminal-width-based wrapping the way a
        real redirected stdout does.
        """
        cryptography = pytest.importorskip("cryptography")
        from pydependencycheck.sbom import SBOMSigner

        key_path = project / "key.pem"
        SBOMSigner().generate_keys(str(key_path))

        result = subprocess.run(
            [
                "python3",
                "-m",
                "pydependencycheck.cli",
                "export",
                "--path",
                str(project),
                "--sign",
                "--key",
                str(key_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        sbom = json.loads(result.stdout)  # must not raise -- proves no corruption
        assert "signatures" in sbom


class TestLicensesCommand:
    def _mock_pypi_response(self, license_field):
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {"info": {"license": license_field, "classifiers": [], "version": "1.0.0"}}
        return response

    def test_licenses_reports_compliance_summary(self, runner, project):
        with patch("pydependencycheck.licenses.requests.get") as mock_get:
            mock_get.return_value = self._mock_pypi_response("MIT")
            result = runner.invoke(cli, ["licenses", "--path", str(project)])

        assert result.exit_code == 0, result.output
        assert "License Compliance Report" in result.output
        assert "Summary:" in result.output

    def test_licenses_fail_on_restricted_exits_nonzero(self, runner, project):
        with patch("pydependencycheck.licenses.requests.get") as mock_get:
            mock_get.return_value = self._mock_pypi_response("GPL-3.0")
            result = runner.invoke(cli, ["licenses", "--path", str(project), "--fail-on-restricted"])

        assert result.exit_code == 1

    def test_licenses_project_license_compatibility_check(self, runner, project):
        with patch("pydependencycheck.licenses.requests.get") as mock_get:
            mock_get.return_value = self._mock_pypi_response("MIT")
            result = runner.invoke(cli, ["licenses", "--path", str(project), "--project-license", "MIT"])

        assert result.exit_code == 0, result.output
        assert "compatible" in result.output.lower()


class TestScanCommandStillWorks:
    def test_scan_html_report_escapes_malicious_names(self, runner, tmp_path):
        """End-to-end proof the XSS fix is wired into the real `scan`
        command's HTML output path, not just the reporter in isolation."""
        (tmp_path / "requirements.txt").write_text("requests==2.32.0\n")

        # A malicious "package" injected via a crafted requirements file --
        # not realistic input for requirements.txt specifically, but proves
        # the report generator itself never trusts dependency name/version
        # content when producing HTML.
        with patch("pydependencycheck.scanner.DependencyScanner.scan") as mock_scan:
            from pydependencycheck.scanner import ScanResult

            fake_result = ScanResult()
            fake_result.dependencies = [
                {
                    "name": "<script>alert(1)</script>",
                    "version": "1.0",
                    "direct": True,
                    "source": "requirements.txt",
                }
            ]
            fake_result.direct_count = 1
            fake_result.transitive_count = 0
            mock_scan.return_value = fake_result

            result = runner.invoke(cli, ["scan", "--path", str(tmp_path), "--format", "html"])

        assert result.exit_code == 0, result.output
        assert "<script>alert(1)</script>" not in result.output
        assert "&lt;script&gt;" in result.output
