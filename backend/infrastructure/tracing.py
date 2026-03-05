"""OpenTelemetry tracing configuration for VerifID.

Exports spans to Jaeger via OTLP. Provides helpers to create spans
for pipeline phases and ML model inference.
"""

import os
from contextlib import contextmanager
from typing import Any, Generator

import structlog

logger = structlog.get_logger()

# Lazy-loaded tracer — avoids import errors if OTel is not installed.
_tracer = None


def _get_tracer():
    global _tracer
    if _tracer is not None:
        return _tracer

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        env = os.getenv("APP_ENV", "development")
        jaeger_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
        sample_rate = 1.0 if env == "development" else 0.1

        resource = Resource.create({
            "service.name": "verifid-api",
            "service.version": "0.1.0",
            "deployment.environment": env,
        })

        provider = TracerProvider(resource=resource)

        # Configure sampling
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
        provider = TracerProvider(
            resource=resource,
            sampler=TraceIdRatioBased(sample_rate),
        )

        exporter = OTLPSpanExporter(endpoint=jaeger_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("verifid", "0.1.0")

        logger.info("tracing.initialized", endpoint=jaeger_endpoint, sample_rate=sample_rate)
    except ImportError:
        logger.warning("tracing.otel_not_installed", msg="OpenTelemetry SDK not available, tracing disabled")
        _tracer = _NoopTracer()
    except Exception:
        logger.exception("tracing.init_failed")
        _tracer = _NoopTracer()

    return _tracer


class _NoopSpan:
    """No-op span for when OTel is not available."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, status: Any) -> None:
        pass

    def record_exception(self, exc: Exception) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _NoopTracer:
    """No-op tracer for when OTel is not available."""

    def start_as_current_span(self, name: str, **kwargs):
        return _NoopSpan()


def get_tracer():
    """Get the configured tracer (or noop if OTel unavailable)."""
    return _get_tracer()


@contextmanager
def trace_pipeline_phase(session_id: str, phase: str) -> Generator:
    """Create a span for a pipeline phase."""
    tracer = get_tracer()
    with tracer.start_as_current_span(f"pipeline.{phase}") as span:
        span.set_attribute("session.id", session_id)
        span.set_attribute("pipeline.phase", phase)
        yield span


@contextmanager
def trace_ml_inference(model_name: str, session_id: str = "") -> Generator:
    """Create a span for ML model inference."""
    tracer = get_tracer()
    with tracer.start_as_current_span(f"ml.inference.{model_name}") as span:
        span.set_attribute("ml.model", model_name)
        if session_id:
            span.set_attribute("session.id", session_id)
        yield span


def instrument_fastapi(app):
    """Auto-instrument a FastAPI app with OpenTelemetry."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        logger.info("tracing.fastapi_instrumented")
    except ImportError:
        logger.warning("tracing.fastapi_instrumentor_not_available")


def instrument_celery():
    """Auto-instrument Celery with OpenTelemetry."""
    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        CeleryInstrumentor().instrument()
        logger.info("tracing.celery_instrumented")
    except ImportError:
        logger.warning("tracing.celery_instrumentor_not_available")
