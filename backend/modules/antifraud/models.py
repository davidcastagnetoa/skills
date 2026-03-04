"""Pydantic schemas for the antifraud module."""

from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskFlag(BaseModel):
    """A specific risk indicator detected during antifraud analysis."""

    code: str
    message: str
    level: RiskLevel = RiskLevel.LOW
    score_impact: float = Field(ge=0.0, le=1.0, default=0.0)


class RecommendedAction(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    REJECT = "reject"


class BlacklistCheckResult(BaseModel):
    is_blacklisted: bool = False
    reason: str | None = None


class MultiAttemptResult(BaseModel):
    is_suspicious: bool = False
    attempts_count: int = 0
    different_documents: int = 0
    time_window_minutes: int = 60


class GeoCheckResult(BaseModel):
    ip_country: str | None = None
    document_nationality: str | None = None
    is_discrepant: bool = False
    is_vpn: bool = False
    is_proxy: bool = False
    is_tor: bool = False


class AgeConsistencyResult(BaseModel):
    estimated_age: int | None = None
    document_age: int | None = None
    discrepancy_years: int = 0
    is_suspicious: bool = False


class AntifraudResult(BaseModel):
    """Complete antifraud analysis result."""

    fraud_score: float = Field(ge=0.0, le=1.0, default=0.0)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    recommended_action: RecommendedAction = RecommendedAction.ALLOW
    blacklist: BlacklistCheckResult = Field(default_factory=BlacklistCheckResult)
    multi_attempt: MultiAttemptResult = Field(default_factory=MultiAttemptResult)
    geo_check: GeoCheckResult = Field(default_factory=GeoCheckResult)
    age_consistency: AgeConsistencyResult = Field(default_factory=AgeConsistencyResult)
    processing_time_ms: int = 0
