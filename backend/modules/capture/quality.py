"""Image quality validation for captured selfies and documents."""

import cv2
import numpy as np
import structlog

from modules.capture.models import CaptureQualityResult, QualityIssue

logger = structlog.get_logger()

# Thresholds
_MIN_SHARPNESS = 100.0  # Laplacian variance
_MIN_BRIGHTNESS = 40.0
_MAX_BRIGHTNESS = 220.0
_MIN_WIDTH = 640
_MIN_HEIGHT = 480
_MAX_PAYLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

# Haar cascade for quick face presence check
_FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"  # type: ignore[attr-defined]


def validate_image_quality(image: np.ndarray) -> CaptureQualityResult:
    """Validate the quality of a captured image.

    Checks:
    - Sharpness (Laplacian variance > 100)
    - Brightness (mean intensity 40-220)
    - Resolution (minimum 640x480)
    - Face presence (exactly 1 face)
    """
    issues: list[QualityIssue] = []
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # Sharpness
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if sharpness < _MIN_SHARPNESS:
        issues.append(QualityIssue(
            code="too_blurry",
            message=f"Image is too blurry (sharpness: {sharpness:.0f}, min: {_MIN_SHARPNESS})",
        ))

    # Brightness
    brightness = float(np.mean(gray))
    if brightness < _MIN_BRIGHTNESS:
        issues.append(QualityIssue(
            code="too_dark",
            message=f"Image is too dark (brightness: {brightness:.0f})",
        ))
    elif brightness > _MAX_BRIGHTNESS:
        issues.append(QualityIssue(
            code="too_bright",
            message=f"Image is overexposed (brightness: {brightness:.0f})",
        ))

    # Resolution
    resolution_ok = w >= _MIN_WIDTH and h >= _MIN_HEIGHT
    if not resolution_ok:
        issues.append(QualityIssue(
            code="low_resolution",
            message=f"Resolution too low ({w}x{h}, min: {_MIN_WIDTH}x{_MIN_HEIGHT})",
        ))

    # Face detection
    cascade = cv2.CascadeClassifier(_FACE_CASCADE_PATH)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    face_count = len(faces)
    face_detected = face_count >= 1

    if face_count == 0:
        issues.append(QualityIssue(
            code="no_face_detected",
            message="No face detected in the image",
        ))
    elif face_count > 1:
        issues.append(QualityIssue(
            code="multiple_faces",
            message=f"Multiple faces detected ({face_count}), expected exactly 1",
            severity="warning",
        ))

    # Quality score
    sharpness_score = min(sharpness / 300.0, 1.0)
    if _MIN_BRIGHTNESS <= brightness <= _MAX_BRIGHTNESS:
        brightness_score = 1.0
    else:
        brightness_score = 0.3
    resolution_score = 1.0 if resolution_ok else 0.3
    face_score = 1.0 if face_count == 1 else (0.5 if face_count > 1 else 0.0)

    quality_score = (
        sharpness_score * 0.3
        + brightness_score * 0.2
        + resolution_score * 0.2
        + face_score * 0.3
    )

    is_valid = len([i for i in issues if i.severity == "error"]) == 0

    return CaptureQualityResult(
        is_valid=is_valid,
        quality_score=round(quality_score, 4),
        issues=issues,
        sharpness=round(sharpness, 2),
        brightness=round(brightness, 2),
        resolution_ok=resolution_ok,
        face_detected=face_detected,
        face_count=face_count,
    )


def validate_payload_size(data: bytes) -> QualityIssue | None:
    """Check that the image payload is within size limits."""
    if len(data) > _MAX_PAYLOAD_BYTES:
        size_mb = len(data) / (1024 * 1024)
        return QualityIssue(
            code="payload_too_large",
            message=f"Image too large ({size_mb:.1f} MB, max: 10 MB)",
        )
    return None
