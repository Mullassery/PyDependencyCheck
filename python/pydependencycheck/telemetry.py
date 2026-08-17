"""OpenTelemetry instrumentation for observability"""

import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime

# Optional OTEL imports
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

# These exporters pull in optional, heavier dependencies (grpc, prometheus
# client, jaeger thrift) that aren't required for local/CI usage of the
# "console" exporter, so they're imported lazily and independently guarded.
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

    HAS_OTLP = True
except ImportError:
    HAS_OTLP = False

try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter

    HAS_JAEGER = True
except ImportError:
    HAS_JAEGER = False

try:
    from opentelemetry.exporter.prometheus import PrometheusMetricReader

    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

logger = logging.getLogger(__name__)


class TelemetryConfig:
    """Configuration for OpenTelemetry instrumentation"""

    def __init__(
        self,
        enabled: bool = False,
        exporter: str = "console",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
        otlp_endpoint: str = "http://localhost:4317",
    ):
        self.enabled = enabled and HAS_OTEL
        # "console" prints real spans/metrics to stdout via the OTEL SDK's
        # own exporters -- no collector required, so it works out of the box
        # and is what CI / local runs should default to. "stdout" is kept as
        # an alias for backwards compatibility.
        self.exporter = "console" if exporter == "stdout" else exporter  # "console", "jaeger", "otlp", "prometheus"
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
        """Setup distributed tracing.

        "console" (the default) always works out of the box: it uses the
        OTEL SDK's own ConsoleSpanExporter, so traces are real and visible
        with no collector required. "jaeger"/"otlp" are tracing-capable
        backends; if their exporter package isn't installed or the exporter
        choice doesn't apply to tracing (e.g. "prometheus", which is
        metrics-only), we fall back to the console exporter so tracing stays
        enabled and genuinely producing output rather than silently no-op.
        """
        provider = TracerProvider()
        processor = None

        if self.config.exporter == "jaeger":
            if HAS_JAEGER:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=self.config.jaeger_host,
                    agent_port=self.config.jaeger_port,
                )
                processor = BatchSpanProcessor(jaeger_exporter)
            else:
                logger.warning(
                    "jaeger exporter not installed (pip install opentelemetry-exporter-jaeger); "
                    "falling back to console tracing"
                )
        elif self.config.exporter == "otlp":
            if HAS_OTLP:
                otlp_exporter = OTLPSpanExporter(endpoint=self.config.otlp_endpoint)
                processor = BatchSpanProcessor(otlp_exporter)
            else:
                logger.warning(
                    "otlp exporter not installed (pip install opentelemetry-exporter-otlp); "
                    "falling back to console tracing"
                )

        if processor is None:
            processor = SimpleSpanProcessor(ConsoleSpanExporter())

        try:
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            self.tracer = trace.get_tracer(__name__)
            logger.info(f"Tracing enabled with {self.config.exporter} exporter")
        except Exception as e:
            logger.warning(f"Failed to setup tracing: {e}")
            self.enabled = False

    def _setup_metrics(self) -> None:
        """Setup metrics collection (same fallback-to-console strategy as tracing)."""
        reader = None

        if self.config.exporter == "prometheus":
            if HAS_PROMETHEUS:
                reader = PrometheusMetricReader()
            else:
                logger.warning(
                    "prometheus exporter not installed (pip install opentelemetry-exporter-prometheus); "
                    "falling back to console metrics"
                )
        elif self.config.exporter == "otlp":
            if HAS_OTLP:
                otlp_metric_exporter = OTLPMetricExporter(endpoint=self.config.otlp_endpoint)
                reader = PeriodicExportingMetricReader(otlp_metric_exporter)
            else:
                logger.warning(
                    "otlp exporter not installed (pip install opentelemetry-exporter-otlp); "
                    "falling back to console metrics"
                )

        if reader is None:
            reader = PeriodicExportingMetricReader(ConsoleMetricExporter(), export_interval_millis=60_000)

        try:
            metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))
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
                "pydep_total_dependencies", description="Total dependencies scanned", unit="1"
            )
            dep_counter.add(total_deps)

            direct_counter = self.meter.create_counter(
                "pydep_direct_dependencies", description="Direct dependencies", unit="1"
            )
            direct_counter.add(direct_deps)

            # Gauge for health score. Note: the OTEL Python SDK's
            # synchronous Gauge instrument uses `.set()`, not `.record()`
            # (unlike Counter/Histogram) -- calling `.record()` raises
            # AttributeError, which was previously being silently
            # swallowed by the broad except below, so this metric was
            # never actually emitted.
            health_gauge = self.meter.create_gauge(
                "pydep_health_score", description="Dependency health score (0-100)", unit="1"
            )
            health_gauge.set(health_score)

        except Exception as e:
            logger.debug(f"Failed to record metrics: {e}")

    def record_vulnerability_metric(self, critical: int, high: int, medium: int, low: int) -> None:
        """Record vulnerability metrics"""
        if not self.enabled or not self.meter:
            return

        try:
            critical_counter = self.meter.create_counter(
                "pydep_vulnerabilities_critical", description="Critical vulnerabilities", unit="1"
            )
            critical_counter.add(critical)

            high_counter = self.meter.create_counter(
                "pydep_vulnerabilities_high", description="High severity vulnerabilities", unit="1"
            )
            high_counter.add(high)

            medium_counter = self.meter.create_counter(
                "pydep_vulnerabilities_medium", description="Medium severity vulnerabilities", unit="1"
            )
            medium_counter.add(medium)

            low_counter = self.meter.create_counter(
                "pydep_vulnerabilities_low", description="Low severity vulnerabilities", unit="1"
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
                "pydep_operation_duration_ms", description="Operation duration in milliseconds", unit="ms"
            )
            duration_histogram.record(duration_ms, {"operation": operation})

        except Exception as e:
            logger.debug(f"Failed to record performance metric: {e}")

    def shutdown(self) -> None:
        """Flush and shut down telemetry providers.

        PyDependencyCheck runs as a short-lived CLI process, so buffered
        spans/metrics (e.g. the periodic console metric reader) need an
        explicit flush before exit or they'd never actually be emitted.
        Call this once at the end of a CLI invocation that enabled telemetry.
        """
        if not self.enabled:
            return

        try:
            provider = trace.get_tracer_provider()
            if hasattr(provider, "force_flush"):
                provider.force_flush()
        except Exception as e:
            logger.debug(f"Failed to flush tracer provider: {e}")

        try:
            meter_provider = metrics.get_meter_provider()
            if hasattr(meter_provider, "force_flush"):
                meter_provider.force_flush()
            if hasattr(meter_provider, "shutdown"):
                meter_provider.shutdown()
        except Exception as e:
            logger.debug(f"Failed to flush meter provider: {e}")


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
