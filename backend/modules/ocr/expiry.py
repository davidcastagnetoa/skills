"""Document expiry validator."""

from datetime import date, timedelta

import structlog

from modules.ocr.models import ExpiryResult

logger = structlog.get_logger()

_WARNING_DAYS = 30


def validate_expiry(expiry_date_iso: str | None) -> ExpiryResult:
    """Check if a document is expired or about to expire.

    Args:
        expiry_date_iso: Expiry date in ISO 8601 format (YYYY-MM-DD).

    Returns:
        ExpiryResult with expiry status and optional warning.
    """
    if not expiry_date_iso:
        return ExpiryResult()

    try:
        expiry = date.fromisoformat(expiry_date_iso)
    except ValueError:
        logger.warning("expiry_validator.invalid_date", date=expiry_date_iso)
        return ExpiryResult()

    today = date.today()
    delta = (expiry - today).days

    if delta < 0:
        logger.info("expiry_validator.document_expired", days_ago=abs(delta))
        return ExpiryResult(
            is_expired=True,
            days_until_expiry=delta,
            warning="document_expired",
        )

    if delta <= _WARNING_DAYS:
        logger.info("expiry_validator.expiring_soon", days_left=delta)
        return ExpiryResult(
            is_expired=False,
            days_until_expiry=delta,
            warning="expires_within_30_days",
        )

    return ExpiryResult(
        is_expired=False,
        days_until_expiry=delta,
    )
