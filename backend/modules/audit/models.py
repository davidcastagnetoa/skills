"""Pydantic schemas for the audit module."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    SESSION_CREATED = "session_created"
    CAPTURE_VALIDATED = "capture_validated"
    LIVENESS_COMPLETED = "liveness_completed"
    DOC_PROCESSING_COMPLETED = "doc_processing_completed"
    OCR_COMPLETED = "ocr_completed"
    FACE_MATCH_COMPLETED = "face_match_completed"
    ANTIFRAUD_COMPLETED = "antifraud_completed"
    DECISION_MADE = "decision_made"
    SESSION_COMPLETED = "session_completed"
    SESSION_ERROR = "session_error"
    DATA_PURGED = "data_purged"


class AuditEvent(BaseModel):
    """A single audit event in the session trail."""

    session_id: str
    trace_id: str | None = None
    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict = Field(default_factory=dict)
    anonymized: bool = False


class AuditTrail(BaseModel):
    """Complete audit trail for a verification session."""

    session_id: str
    events: list[AuditEvent] = Field(default_factory=list)
    integrity_hash: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
