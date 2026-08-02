"""OpenTelemetry instrumentation for observability"""

import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime

# Optional OTEL imports
try:
    from opentelemetry import trace, metrics
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

logger = logging.getLogger(__name__)


class TelemetryConfig:
    """Configuration for OpenTelemetry instrumentation"""

    def __init__(self, enabled: bool = False, exporter: str = "stdout",
                 jaeger_host: str = "localhost", jaeger_port: int = 6831,
                 otlp_endpoint: str = "http://localhost:4317"):
        self.enabled = enabled and HAS_OTEL
        self.exporter = exporter  # "jaeger", "otlp", "prometheus", "stdout"
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.otlp_endpoint = otlp_endpoint

        if enabled and not HAS_OTEL:
            logger.warning("OpenTelemetry not installed. Install with: pip install opentelemetry-api opentelemetry-sdk")


class TelemetryManager:
    """Manages OpenTelemetry instrumentation"""

    def __init__(self, config: TelemetryConfig):
        self.config = config
        self.tracer: Optional[Any] = None
        self.meter: Optional[Any] = None
        self.enabled = config.enabled

        if self.enabled:
            self._setup_tracing()
            self._setup_metrics()

    def _setup_tracing(self) -> None:
        """Setup distributed tracing"""
        try:
            if self.config.exporter == "jaeger":
                jaeger_exporter = JaegerExporter(
                    agent_host_name=self.config.jaeger_host,
                    agent_port=self.config.jaeger_port,
                )
                trace.set_tracer_provider(TracerProvider())
                trace.get_tracer_provider().add_span_processor(
                    BatchSpanProcessor(jaeger_exporter)
                )

            elif self.config.exporter == "otlp":
                otlp_exporter = OTLPSpanExporter(endpoint=self.config.otlp_endpoint)
                trace.set_tracer_provider(TracerProvider())
                trace.get_tracer_provider().add_span_processor(
                    BatchSpanProcessor(otlp_exporter)
                )

            self.tracer = trace.get_tracer(__name__)
            logger.info(f"Tracing enabled with {self.config.exporter} exporter")

        except Exception as e:
            logger.warning(f"Failed to setup tracing: {e}")
            self.enabled = False

    def _setup_metrics(self) -> None:
        """Setup metrics collection"""
        try:
            if self.config.exporter == "prometheus":
                prometheus_reader = PrometheusMetricReader()
                metrics.set_meter_provider(MeterProvider(metric_readers=[prometheus_reader]))

            elif self.config.exporter == "otlp":
                otlp_metric_exporter = OTLPMetricExporter(endpoint=self.config.otlp_endpoint)
                otlp_reader = PeriodicExportingMetricReader(otlp_metric_exporter)
                metrics.set_meter_provider(MeterProvider(metric_readers=[otlp_reader]))

            self.meter = metrics.get_meter(__name__)
            logger.info(f"Metrics enabled with {self.config.exporter} exporter")

        except Exception as e:
            logger.warning(f"Failed to setup metrics: {e}")

    @contextmanager
    def trace_scan(self, project_path: str):
        """Trace a dependency scan operation"""
        if not self.enabled or not self.tracer:
            yield
            return

        with self.tracer.start_as_current_span("scan_dependencies") as span:
            span.set_attribute("project_path", project_path)
            span.set_attribute("timestamp", datetime.now().isoformat())

            try:
                yield span
                span.set_attribute("status", "success")
            except Exception as e:
                span.set_attribute("status", "error")
                span.set_attribute("error", str(e))
                raise

    @contextmanager
    def trace_git_blame(self, package: str):
        """Trace git blame operation"""
        if not self.enabled or not self.tracer:
            yield
            return

        with self.tracer.start_as_current_span("git_blame") as span:
            span.set_attribute("package", package)

            try:
                yield span
                span.set_attribute("status", "success")
            except Exception as e:
                span.set_attribute("status", "error")
                raise

    @contextmanager
    def trace_vulnerability_scan(self, package: str):
        """Trace vulnerability scanning"""
        if not self.enabled or not self.tracer:
            yield
            return

        with self.tracer.start_as_current_span("scan_vulnerabilities") as span:
            span.set_attribute("package", package)

            try:
                yield span
                span.set_attribute("status", "success")
            except Exception as e:
                span.set_attribute("status", "error")
                raise

    def record_scan_metric(self, total_deps: int, direct_deps: int, health_score: int) -> None:
        """Record scan metrics"""
        if not self.enabled or not self.meter:
            return

        try:
            # Counters
            dep_counter = self.meter.create_counter(
                "pydep_total_dependencies",
                description="Total dependencies scanned",
                unit="1"
            )
            dep_counter.add(total_deps)

            direct_counter = self.meter.create_counter(
                "pydep_direct_dependencies",
                description="Direct dependencies",
                unit="1"
            )
            direct_counter.add(direct_deps)

            # Gauge for health score
            health_gauge = self.meter.create_gauge(
                "pydep_health_score",
                description="Dependency health score (0-100)",
                unit="1"
            )
            health_gauge.record(health_score)

        except Exception as e:
            logger.debug(f"Failed to record metrics: {e}")

    def record_vulnerability_metric(self, critical: int, high: int, medium: int, low: int) -> None:
        """Record vulnerability metrics"""
        if not self.enabled or not self.meter:
            return

        try:
            critical_counter = self.meter.create_counter(
                "pydep_vulnerabilities_critical",
                description="Critical vulnerabilities",
                unit="1"
            )
            critical_counter.add(critical)

            high_counter = self.meter.create_counter(
                "pydep_vulnerabilities_high",
                description="High severity vulnerabilities",
                unit="1"
            )
            high_counter.add(high)

            medium_counter = self.meter.create_counter(
                "pydep_vulnerabilities_medium",
                description="Medium severity vulnerabilities",
                unit="1"
            )
            medium_counter.add(medium)

            low_counter = self.meter.create_counter(
                "pydep_vulnerabilities_low",
                description="Low severity vulnerabilities",
                unit="1"
            )
            low_counter.add(low)

        except Exception as e:
            logger.debug(f"Failed to record vulnerability metrics: {e}")

    def record_performance_metric(self, operation: str, duration_ms: float) -> None:
        """Record performance metrics"""
        if not self.enabled or not self.meter:
            return

        try:
            duration_histogram = self.meter.create_histogram(
                "pydep_operation_duration_ms",
                description="Operation duration in milliseconds",
                unit="ms"
            )
            duration_histogram.record(duration_ms, {"operation": operation})

        except Exception as e:
            logger.debug(f"Failed to record performance metric: {e}")


# Global telemetry instance
_telemetry: Optional[TelemetryManager] = None


def init_telemetry(config: TelemetryConfig) -> None:
    """Initialize global telemetry"""
    global _telemetry
    _telemetry = TelemetryManager(config)


def get_telemetry() -> TelemetryManager:
    """Get global telemetry instance"""
    global _telemetry
    if _telemetry is None:
        _telemetry = TelemetryManager(TelemetryConfig(enabled=False))
    return _telemetry


def is_telemetry_enabled() -> bool:
    """Check if telemetry is enabled"""
    return get_telemetry().enabled
