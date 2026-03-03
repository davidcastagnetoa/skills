import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from api.config import settings
from api.dependencies import Cache, DBSession, Limiter
from core.exceptions import RateLimitExceededError, SessionNotFoundError
from core.schemas import (
    VerificationCreated,
    VerificationRequest,
    VerificationResponse,
    VerificationStatus,
)
from infrastructure.models import VerificationSession

router = APIRouter(prefix="/api/v1", tags=["verification"])


@router.post(
    "/verify",
    response_model=VerificationCreated,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_verification(
    request: Request,
    body: VerificationRequest,
    db: DBSession,
    cache: Cache,
    limiter: Limiter,
) -> VerificationCreated:
    """Start a new identity verification session."""
    # Rate limiting by IP
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"rate:verify:{client_ip}"
    allowed = await limiter.check(
        rate_key,
        max_requests=settings.rate_limit_verify_requests,
        window_seconds=settings.rate_limit_verify_window_seconds,
    )
    if not allowed:
        raise RateLimitExceededError(retry_after=settings.rate_limit_verify_window_seconds)

    # Create session
    session_id = uuid.uuid4()
    session = VerificationSession(
        id=session_id,
        status="pending",
        client_id="default",  # TODO: extract from JWT in Phase 4
        device_fingerprint=body.device_fingerprint,
        ip_address=client_ip,
        metadata_=body.metadata,
    )
    db.add(session)
    await db.flush()

    # Cache session state
    await cache.set(
        f"session:{session_id}",
        {
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        ttl=settings.pipeline_timeout_seconds * 2,
    )

    # TODO: Phase 3 — dispatch pipeline tasks via Celery

    return VerificationCreated(session_id=session_id)


@router.get(
    "/verify/{session_id}",
    response_model=VerificationResponse,
)
async def get_verification(
    session_id: uuid.UUID,
    db: DBSession,
    cache: Cache,
) -> VerificationResponse:
    """Get the status and result of a verification session."""
    # Try cache first
    cached = await cache.get(f"session:{session_id}")
    if cached and isinstance(cached, dict) and cached.get("status") == "pending":
        return VerificationResponse(
            session_id=session_id,
            status=VerificationStatus.PENDING,
            timestamp=datetime.now(timezone.utc),
        )

    # Fallback to database
    from sqlalchemy import select

    stmt = select(VerificationSession).where(VerificationSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if session is None:
        raise SessionNotFoundError(f"Session {session_id} not found")

    return VerificationResponse(
        session_id=session.id,
        status=VerificationStatus(session.status),
        confidence_score=session.confidence_score,
        processing_time_ms=session.processing_time_ms,
        timestamp=session.updated_at,
    )
