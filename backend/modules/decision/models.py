"""Pydantic schemas for the decision engine module."""

from enum import Enum

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class HardRuleResult(BaseModel):
    """Result of hard rule evaluation."""

    triggered: bool = False
    rule_code: str | None = None
    reason: str | None = None


class ScoreBreakdown(BaseModel):
    """Breakdown of the weighted score calculation."""

    liveness_score: float = 0.0
    liveness_weighted: float = 0.0
    face_match_score: float = 0.0
    face_match_weighted: float = 0.0
    document_integrity_score: float = 0.0
    document_integrity_weighted: float = 0.0
    ocr_consistency_score: float = 0.0
    ocr_consistency_weighted: float = 0.0
    antifraud_score: float = 0.0
    antifraud_weighted: float = 0.0
    global_score: float = 0.0


class DecisionReason(BaseModel):
    """A human-readable reason contributing to the decision."""

    module: str
    message: str
    impact: str = "neutral"  # "positive", "negative", "neutral"


class DecisionResult(BaseModel):
    """Complete decision engine result."""

    status: VerificationStatus = VerificationStatus.REJECTED
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)
    reasons: list[DecisionReason] = Field(default_factory=list)
    hard_rule: HardRuleResult = Field(default_factory=HardRuleResult)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    processing_time_ms: int = 0
