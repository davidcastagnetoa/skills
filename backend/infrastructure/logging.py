"""Structured logging configuration with trace correlation.

Configures structlog to emit JSON logs with session_id, trace_id,
and span_id for cross-service correlation.
"""

import os

import structlog


def configure_logging(env: str = "development", log_level: str = "INFO") -> None:
    """Configure structlog for the application.

    Args:
        env: Environment name (development, staging, production).
        log_level: Minimum log level.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        _add_trace_context,
    ]

    if env == "development":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            structlog.get_level_from_name(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _add_trace_context(logger, method_name, event_dict):
    """Add OpenTelemetry trace context to log events."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
    except ImportError:
        pass
    return event_dict


def bind_session_context(session_id: str) -> None:
    """Bind session_id to structlog context for all subsequent logs."""
    structlog.contextvars.bind_contextvars(session_id=session_id)


def clear_session_context() -> None:
    """Clear session context from structlog."""
    structlog.contextvars.unbind_contextvars("session_id")
