import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VerificationStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    VERIFIED = "verified"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"
    ERROR = "error"


class ModuleStatusEnum(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


class VerificationSession(Base):
    __tablename__ = "verification_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(
        Enum(VerificationStatusEnum, name="verification_status"),
        default=VerificationStatusEnum.PENDING,
        nullable=False,
    )
    client_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    results: Mapped[list["VerificationResult"]] = relationship(back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sessions_client_created", "client_id", "created_at"),
        Index("ix_sessions_device_created", "device_fingerprint", "created_at"),
        Index("ix_sessions_ip_created", "ip_address", "created_at"),
    )


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_sessions.id", ondelete="CASCADE"), nullable=False
    )
    module_name: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(ModuleStatusEnum, name="module_status"),
        nullable=False,
    )
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    session: Mapped["VerificationSession"] = relationship(back_populates="results")

    __table_args__ = (Index("ix_results_session", "session_id"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hmac_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class BlacklistedDocument(Base):
    __tablename__ = "blacklisted_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    added_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class APIClient(Base):
    __tablename__ = "api_clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    permissions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rate_limit: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
