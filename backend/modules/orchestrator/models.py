"""Pydantic schemas for the pipeline orchestrator."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class PipelinePhase(str, Enum):
    CAPTURE_VALIDATION = "capture_validation"
    LIVENESS = "liveness"
    DOC_PROCESSING = "doc_processing"
    FACE_MATCH = "face_match"
    OCR = "ocr"
    ANTIFRAUD = "antifraud"
    DECISION = "decision"


class PhaseResult(BaseModel):
    """Result from a single pipeline phase."""

    phase: PipelinePhase
    success: bool = True
    score: float = 0.0
    error: str | None = None
    processing_time_ms: int = 0
    details: dict = Field(default_factory=dict)


class SessionProgress(BaseModel):
    """Current progress of a verification session."""

    session_id: str
    current_phase: PipelinePhase | None = None
    phases_completed: list[PipelinePhase] = Field(default_factory=list)
    started_at: datetime | None = None
    elapsed_ms: int = 0


class PipelineResult(BaseModel):
    """Final result from the full pipeline."""

    session_id: str
    status: str  # VERIFIED / REJECTED / MANUAL_REVIEW / ERROR
    confidence_score: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    module_scores: dict[str, float] = Field(default_factory=dict)
    phase_results: list[PhaseResult] = Field(default_factory=list)
    processing_time_ms: int = 0
    integrity_hash: str | None = None
