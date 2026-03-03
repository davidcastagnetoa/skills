import enum
from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    VERIFIED = "verified"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"
    ERROR = "error"


class ModuleStatus(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


class VerificationRequest(BaseModel):
    """Request to start a verification session."""

    selfie_image: str = Field(..., description="Base64-encoded selfie image")
    document_image: str = Field(..., description="Base64-encoded document image")
    device_fingerprint: str | None = Field(None, description="SHA256 hash of device info")
    metadata: dict[str, str] | None = Field(None, description="Additional client metadata")


class ModuleScore(BaseModel):
    """Score from a single pipeline module."""

    module_name: str
    score: float = Field(ge=0.0, le=1.0)
    status: ModuleStatus
    details: dict[str, object] = Field(default_factory=dict)
    processing_time_ms: int = 0


class VerificationResponse(BaseModel):
    """Response from a verification session."""

    session_id: UUID
    status: VerificationStatus
    confidence_score: float | None = None
    reasons: list[str] = Field(default_factory=list)
    modules_scores: dict[str, float] | None = None
    processing_time_ms: int | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VerificationCreated(BaseModel):
    """Response when a verification session is created."""

    session_id: UUID = Field(default_factory=uuid4)
    status: VerificationStatus = VerificationStatus.PENDING
    message: str = "Verification session created"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    checks: dict[str, bool] = Field(default_factory=dict)
