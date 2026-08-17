"""Tests for OpenTelemetry instrumentation.

Uses the "console" exporter, which uses the OTEL SDK's own
ConsoleSpanExporter/ConsoleMetricExporter and therefore requires no
external collector -- these are real spans/metrics being created and
exported, just captured from stdout instead of shipped over the network.

The tracer/meter providers OTEL configures are process-global singletons
that can only be set once per process. That's a non-issue for the real
CLI (one TelemetryManager per process invocation), but it makes in-process
pytest capture fixtures (capsys/capfd) unreliable across multiple tests in
the same session -- provider state and buffered output leak between tests
in ways that don't reflect anything wrong with the actual feature. The
tests that need to observe real console output therefore run in a fresh
subprocess per test, which is slower but verifies the exact same code path
a real `pydependencycheck ... --otel` invocation takes.
"""

import json
import subprocess
import sys

import pytest

from pydependencycheck.telemetry import TelemetryConfig, TelemetryManager, HAS_OTEL

pytestmark = pytest.mark.skipif(not HAS_OTEL, reason="opentelemetry-api/sdk not installed")


def _run_in_subprocess(code: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)


def _first_json_object(text: str) -> dict:
    """Decode just the first JSON document from stdout.

    The OTEL SDK's own self-diagnostics (its "how many spans did I export"
    metrics) get printed to the same console exporter right alongside our
    application's span/metric output, so stdout can contain several
    concatenated JSON documents rather than exactly one.
    """
    obj, _ = json.JSONDecoder().raw_decode(text)
    return obj


class TestTelemetryConfig:
    def test_disabled_by_default(self):
        config = TelemetryConfig()
        assert config.enabled is False

    def test_stdout_is_aliased_to_console(self):
        config = TelemetryConfig(enabled=True, exporter="stdout")
        assert config.exporter == "console"


class TestTelemetryManagerTracing:
    def test_enabled_manager_creates_real_tracer(self):
        mgr = TelemetryManager(TelemetryConfig(enabled=True, exporter="console"))
        assert mgr.enabled is True
        assert mgr.tracer is not None

    def test_disabled_manager_has_no_tracer(self):
        mgr = TelemetryManager(TelemetryConfig(enabled=False))
        assert mgr.enabled is False
        assert mgr.tracer is None

    def test_disabled_trace_scan_is_a_noop(self):
        mgr = TelemetryManager(TelemetryConfig(enabled=False))
        with mgr.trace_scan("/some/project"):
            pass  # must not raise, and there is no tracer to record anything


class TestTelemetryManagerMetrics:
    def test_record_scan_metric_does_not_raise(self):
        mgr = TelemetryManager(TelemetryConfig(enabled=True, exporter="console"))
        mgr.record_scan_metric(total_deps=10, direct_deps=5, health_score=80)
        mgr.shutdown()  # avoid leaking a live background exporter thread past the test

    def test_record_vulnerability_metric_does_not_raise(self):
        mgr = TelemetryManager(TelemetryConfig(enabled=True, exporter="console"))
        mgr.record_vulnerability_metric(critical=1, high=2, medium=3, low=4)
        mgr.shutdown()

    def test_disabled_manager_metrics_are_noop(self):
        mgr = TelemetryManager(TelemetryConfig(enabled=False))
        # Must not raise even though no meter was ever created.
        mgr.record_scan_metric(total_deps=1, direct_deps=1, health_score=100)


class TestConsoleExportEndToEnd:
    """Real subprocess-level proof that --otel produces genuine, parseable
    span/metric output with zero external infrastructure."""

    def test_trace_scan_emits_real_span_to_stdout(self):
        code = (
            "from pydependencycheck.telemetry import TelemetryConfig, TelemetryManager\n"
            "mgr = TelemetryManager(TelemetryConfig(enabled=True, exporter='console'))\n"
            "with mgr.trace_scan('/some/project'):\n"
            "    pass\n"
        )
        result = _run_in_subprocess(code)
        assert result.returncode == 0, result.stderr

        span_data = _first_json_object(result.stdout)
        assert span_data["name"] == "scan_dependencies"
        assert span_data["attributes"]["project_path"] == "/some/project"
        assert span_data["attributes"]["status"] == "success"

    def test_trace_scan_records_error_status_on_exception(self):
        code = (
            "from pydependencycheck.telemetry import TelemetryConfig, TelemetryManager\n"
            "mgr = TelemetryManager(TelemetryConfig(enabled=True, exporter='console'))\n"
            "try:\n"
            "    with mgr.trace_scan('/some/project'):\n"
            "        raise ValueError('boom')\n"
            "except ValueError:\n"
            "    pass\n"
        )
        result = _run_in_subprocess(code)
        assert result.returncode == 0, result.stderr

        span_data = _first_json_object(result.stdout)
        assert span_data["attributes"]["status"] == "error"

    def test_prometheus_missing_falls_back_to_console_tracing(self):
        # Even when a metrics-only exporter is requested, tracing should
        # still work (falling back to console) rather than silently
        # disabling telemetry altogether.
        code = (
            "from pydependencycheck.telemetry import TelemetryConfig, TelemetryManager\n"
            "mgr = TelemetryManager(TelemetryConfig(enabled=True, exporter='prometheus'))\n"
            "assert mgr.enabled is True\n"
            "with mgr.trace_scan('/proj'):\n"
            "    pass\n"
        )
        result = _run_in_subprocess(code)
        assert result.returncode == 0, result.stderr
        assert "scan_dependencies" in result.stdout

    def test_record_scan_metric_produces_real_console_metrics_on_shutdown(self):
        code = (
            "from pydependencycheck.telemetry import TelemetryConfig, TelemetryManager\n"
            "mgr = TelemetryManager(TelemetryConfig(enabled=True, exporter='console'))\n"
            "mgr.record_scan_metric(total_deps=10, direct_deps=5, health_score=80)\n"
            "mgr.shutdown()\n"
        )
        result = _run_in_subprocess(code)
        assert result.returncode == 0, result.stderr
        assert "pydep_total_dependencies" in result.stdout
        assert "pydep_health_score" in result.stdout
