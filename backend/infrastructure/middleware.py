"""FastAPI middleware for Prometheus metrics and OpenTelemetry tracing."""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from infrastructure.metrics import (
    REQUEST_COUNT,
    REQUEST_IN_PROGRESS,
    REQUEST_LATENCY,
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware that records HTTP request metrics."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        path = self._normalize_path(request.url.path)

        REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).inc()
        start = time.perf_counter()

        try:
            response = await call_next(request)
            status = str(response.status_code)
        except Exception:
            status = "500"
            raise
        finally:
            duration = time.perf_counter() - start
            REQUEST_LATENCY.labels(method=method, endpoint=path, status=status).observe(duration)
            REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).dec()

        return response

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize path to avoid high cardinality (replace UUIDs)."""
        parts = path.strip("/").split("/")
        normalized = []
        for part in parts:
            # Replace UUID-like segments
            if len(part) == 36 and part.count("-") == 4:
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/" + "/".join(normalized)
