"""Pydantic schemas for the face match module."""

from enum import Enum

from pydantic import BaseModel, Field


class MatchDecision(str, Enum):
    """Face match decision."""

    MATCH = "match"
    NO_MATCH = "no_match"
    REVIEW = "review"


class FaceDetectionResult(BaseModel):
    """Result of face detection in an image."""

    detected: bool = False
    bbox: list[int] = Field(default_factory=list, description="[x1, y1, x2, y2]")
    landmarks: list[list[float]] = Field(
        default_factory=list, description="5 key landmarks [[x,y], ...]"
    )
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    face_count: int = 0


class FaceQuality(BaseModel):
    """Face image quality assessment."""

    score: float = Field(ge=0.0, le=1.0, default=0.0)
    sharpness: float = 0.0
    brightness: float = 0.0
    size_pixels: int = 0
    is_sufficient: bool = False


class FaceMatchResult(BaseModel):
    """Complete face match comparison result."""

    decision: MatchDecision = MatchDecision.NO_MATCH
    similarity_score: float = Field(ge=0.0, le=1.0, default=0.0)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    selfie_quality: FaceQuality = Field(default_factory=FaceQuality)
    document_quality: FaceQuality = Field(default_factory=FaceQuality)
    super_resolution_applied: bool = False
    processing_time_ms: int = 0
