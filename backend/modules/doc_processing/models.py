"""Pydantic schemas for the document processing module."""

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class DocumentDetection(BaseModel):
    """Result of document detection in an image."""

    detected: bool
    document_type: str | None = None  # DNI, PASSPORT, LICENSE
    country: str | None = None  # ISO 3166-1 alpha-2
    bounding_box: BoundingBox | None = None
    confidence: float = 0.0


class ForgeryAnalysis(BaseModel):
    """Result of forgery/manipulation detection."""

    score: float = Field(ge=0.0, le=1.0, description="0=genuine, 1=forged")
    anomalies: list[str] = Field(default_factory=list)
    ela_score: float = 0.0
    copy_move_score: float = 0.0
    exif_suspicious: bool = False
    font_inconsistency_score: float = 0.0
    compression_artifact_score: float = 0.0


class DocumentProcessingResult(BaseModel):
    """Complete result of document processing pipeline."""

    model_config = {"arbitrary_types_allowed": True}

    document_type: str | None = None
    country: str | None = None
    processed_image: bytes | None = Field(None, exclude=True)
    face_region: bytes | None = Field(None, exclude=True)
    forgery_score: float = Field(ge=0.0, le=1.0, default=0.0)
    detected_anomalies: list[str] = Field(default_factory=list)
    quality_metrics: dict[str, float] = Field(default_factory=dict)
    processing_time_ms: int = 0
