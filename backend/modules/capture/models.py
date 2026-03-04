"""Pydantic schemas for the capture validation module."""

from pydantic import BaseModel, Field


class QualityIssue(BaseModel):
    """A specific quality issue found in the captured image."""

    code: str  # e.g., "too_blurry", "too_dark"
    message: str
    severity: str = "error"  # "error" = blocking, "warning" = informational


class CaptureQualityResult(BaseModel):
    """Result of image quality validation."""

    is_valid: bool = False
    quality_score: float = Field(ge=0.0, le=1.0, default=0.0)
    issues: list[QualityIssue] = Field(default_factory=list)
    sharpness: float = 0.0
    brightness: float = 0.0
    resolution_ok: bool = False
    face_detected: bool = False
    face_count: int = 0


class VirtualCameraResult(BaseModel):
    """Result of virtual camera detection."""

    is_virtual: bool = False
    detected_driver: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class GalleryCheckResult(BaseModel):
    """Result of gallery upload detection."""

    is_from_gallery: bool = False
    reasons: list[str] = Field(default_factory=list)


class CaptureValidationResult(BaseModel):
    """Combined capture validation result."""

    is_valid: bool = False
    quality: CaptureQualityResult = Field(default_factory=CaptureQualityResult)
    virtual_camera: VirtualCameraResult = Field(default_factory=VirtualCameraResult)
    gallery_check: GalleryCheckResult = Field(default_factory=GalleryCheckResult)
    issues: list[QualityIssue] = Field(default_factory=list)
