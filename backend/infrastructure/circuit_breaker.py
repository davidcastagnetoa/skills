"""Circuit breaker pattern for external dependency calls.

Prevents cascading failures by short-circuiting calls to failing services.
States: CLOSED → OPEN → HALF_OPEN → CLOSED.
"""

import time
from enum import Enum
from typing import Any, Callable

import structlog

from infrastructure.metrics import CIRCUIT_BREAKER_STATE

logger = structlog.get_logger()


class CircuitState(Enum):
    CLOSED = 0
    HALF_OPEN = 1
    OPEN = 2


class CircuitBreakerError(Exception):
    """Raised when the circuit breaker is open."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Circuit breaker '{name}' is OPEN")


class CircuitBreaker:
    """Circuit breaker for a single dependency.

    Args:
        name: Dependency name (for logging/metrics).
        failure_threshold: Number of failures before opening.
        recovery_timeout: Seconds before transitioning from OPEN to HALF_OPEN.
        window_seconds: Rolling window for counting failures.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 15.0,
        window_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._window_seconds = window_seconds

        self._state = CircuitState.CLOSED
        self._failures: list[float] = []
        self._opened_at: float = 0.0
        self._last_success: float = 0.0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._opened_at >= self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info("circuit_breaker.half_open", name=self.name)
        return self._state

    def record_success(self) -> None:
        """Record a successful call."""
        self._failures.clear()
        self._last_success = time.monotonic()
        if self._state != CircuitState.CLOSED:
            self._state = CircuitState.CLOSED
            CIRCUIT_BREAKER_STATE.labels(dependency=self.name).set(0)
            logger.info("circuit_breaker.closed", name=self.name)

    def record_failure(self) -> None:
        """Record a failed call and potentially open the circuit."""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        self._failures = [t for t in self._failures if t > cutoff]
        self._failures.append(now)

        if self._state == CircuitState.HALF_OPEN:
            self._open_circuit()
        elif len(self._failures) >= self._failure_threshold:
            self._open_circuit()

    def check(self) -> None:
        """Check if a call is allowed. Raises CircuitBreakerError if OPEN."""
        current = self.state
        if current == CircuitState.OPEN:
            raise CircuitBreakerError(self.name)
        # HALF_OPEN: allow one probe request
        # CLOSED: allow all

    def _open_circuit(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = time.monotonic()
        CIRCUIT_BREAKER_STATE.labels(dependency=self.name).set(2)
        logger.warning(
            "circuit_breaker.opened",
            name=self.name,
            failures=len(self._failures),
        )


# Pre-configured breakers for each dependency
_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _breakers:
        configs = {
            "postgresql": {"failure_threshold": 5, "recovery_timeout": 15.0, "window_seconds": 30.0},
            "redis": {"failure_threshold": 3, "recovery_timeout": 10.0, "window_seconds": 15.0},
            "minio": {"failure_threshold": 3, "recovery_timeout": 10.0, "window_seconds": 15.0},
            "model_server": {"failure_threshold": 3, "recovery_timeout": 20.0, "window_seconds": 30.0},
        }
        config = configs.get(name, {"failure_threshold": 5, "recovery_timeout": 15.0})
        _breakers[name] = CircuitBreaker(name=name, **config)
    return _breakers[name]
