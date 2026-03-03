from typing import Any


class VerifIDError(Exception):
    """Base exception for all VerifID errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ValidationError(VerifIDError):
    """Input validation failed."""


class SessionNotFoundError(VerifIDError):
    """Verification session not found."""


class SessionExpiredError(VerifIDError):
    """Verification session has expired."""


class PipelineTimeoutError(VerifIDError):
    """Pipeline exceeded maximum processing time."""


class ModuleError(VerifIDError):
    """A pipeline module failed."""

    def __init__(self, module_name: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.module_name = module_name
        super().__init__(f"[{module_name}] {message}", details)


class RateLimitExceededError(VerifIDError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class StorageError(VerifIDError):
    """Object storage operation failed."""


class ModelLoadError(VerifIDError):
    """ML model failed to load."""
