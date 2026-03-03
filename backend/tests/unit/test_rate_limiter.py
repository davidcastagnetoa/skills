from core.exceptions import RateLimitExceededError


def test_rate_limit_exception() -> None:
    exc = RateLimitExceededError(retry_after=60)
    assert exc.retry_after == 60
    assert "60 seconds" in exc.message


def test_rate_limit_exception_custom() -> None:
    exc = RateLimitExceededError(retry_after=120)
    assert exc.retry_after == 120
