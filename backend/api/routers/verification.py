import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

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
from modules.orchestrator.service import PipelineOrchestrator

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1", tags=["verification"])


async def _run_pipeline_background(
    session_id: str,
    body: VerificationRequest,
    ip_address: str,
    db_session,
    cache_service,
) -> None:
    """Run the pipeline in the background and update session state."""
    orchestrator = PipelineOrchestrator()

    try:
        result = await orchestrator.run(
            session_id=session_id,
            selfie_image_b64=body.selfie_image,
            document_image_b64=body.document_image,
            device_fingerprint=body.device_fingerprint,
            ip_address=ip_address,
        )

        # Update session in cache
        await cache_service.set(
            f"session:{session_id}",
            {
                "status": result.status.lower(),
                "confidence_score": result.confidence_score,
                "reasons": result.reasons,
                "module_scores": result.module_scores,
                "processing_time_ms": result.processing_time_ms,
                "integrity_hash": result.integrity_hash,
            },
            ttl=settings.pipeline_timeout_seconds * 10,
        )

        logger.info(
            "pipeline.completed",
            session_id=session_id,
            status=result.status,
            score=result.confidence_score,
            elapsed_ms=result.processing_time_ms,
        )
    except Exception:
        logger.exception("pipeline.background_error", session_id=session_id)
        await cache_service.set(
            f"session:{session_id}",
            {"status": "error"},
            ttl=settings.pipeline_timeout_seconds * 10,
        )


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
    background_tasks: BackgroundTasks,
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

    # Dispatch pipeline in background
    background_tasks.add_task(
        _run_pipeline_background, str(session_id), body, client_ip, db, cache
    )

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
    # Try cache first (contains pipeline result after completion)
    cached = await cache.get(f"session:{session_id}")
    if cached and isinstance(cached, dict):
        cached_status = cached.get("status", "pending")
        if cached_status == "pending":
            return VerificationResponse(
                session_id=session_id,
                status=VerificationStatus.PENDING,
                timestamp=datetime.now(timezone.utc),
            )
        # Pipeline finished — return full result from cache
        status_map = {
            "verified": VerificationStatus.VERIFIED,
            "rejected": VerificationStatus.REJECTED,
            "manual_review": VerificationStatus.MANUAL_REVIEW,
            "error": VerificationStatus.ERROR,
        }
        return VerificationResponse(
            session_id=session_id,
            status=status_map.get(cached_status, VerificationStatus.ERROR),
            confidence_score=cached.get("confidence_score"),
            reasons=cached.get("reasons", []),
            modules_scores=cached.get("module_scores"),
            processing_time_ms=cached.get("processing_time_ms"),
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
