"""Face image quality assessment and compensation.

Evaluates sharpness, brightness, and resolution of face crops.
Applies ESRGAN super-resolution when document face quality is too low.
"""

import cv2
import numpy as np
import structlog

from modules.face_match.models import FaceQuality

logger = structlog.get_logger()

_MIN_FACE_SIZE = 60  # Minimum face dimension in pixels
_MIN_SHARPNESS = 50.0  # Laplacian variance threshold
_QUALITY_THRESHOLD = 0.5  # Below this → apply super-resolution


def assess_quality(face_image: np.ndarray) -> FaceQuality:
    """Assess the quality of a face image.

    Evaluates:
    - Sharpness (Laplacian variance)
    - Brightness (mean pixel intensity)
    - Size (pixel dimensions)

    Returns:
        FaceQuality with individual metrics and overall score.
    """
    if face_image is None or face_image.size == 0:
        return FaceQuality()

    h, w = face_image.shape[:2]
    gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY) if len(face_image.shape) == 3 else face_image

    # Sharpness via Laplacian variance
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # Brightness (mean luminance)
    brightness = float(np.mean(gray))

    # Size score
    min_dim = min(h, w)
    size_score = min(min_dim / 112.0, 1.0)  # 112px = ideal for ArcFace

    # Sharpness score (normalize: 0-500 range typical)
    sharpness_score = min(sharpness / 300.0, 1.0)

    # Brightness score (ideal: 100-180)
    if 80 <= brightness <= 200:
        brightness_score = 1.0
    elif brightness < 80:
        brightness_score = brightness / 80.0
    else:
        brightness_score = max(0.0, 1.0 - (brightness - 200) / 55.0)

    # Combined quality score
    score = size_score * 0.3 + sharpness_score * 0.5 + brightness_score * 0.2
    is_sufficient = score >= _QUALITY_THRESHOLD and min_dim >= _MIN_FACE_SIZE

    return FaceQuality(
        score=round(min(max(score, 0.0), 1.0), 4),
        sharpness=round(sharpness, 2),
        brightness=round(brightness, 2),
        size_pixels=min_dim,
        is_sufficient=is_sufficient,
    )


def apply_super_resolution(
    image: np.ndarray,
    session=None,  # onnxruntime.InferenceSession (ESRGAN)
    scale: int = 4,
) -> np.ndarray:
    """Apply super-resolution to enhance a low-quality face image.

    Uses ESRGAN ONNX model if available, otherwise falls back to
    bicubic interpolation.

    Args:
        image: BGR face image (low resolution).
        session: ESRGAN ONNX session.
        scale: Upscale factor.

    Returns:
        Enhanced (upscaled) face image.
    """
    if session is not None:
        try:
            return _run_esrgan(image, session)
        except Exception:
            logger.exception("quality.esrgan_failed, falling back to bicubic")

    # Fallback: bicubic upscale + sharpen
    h, w = image.shape[:2]
    upscaled = cv2.resize(image, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

    # Light sharpening to compensate for interpolation blur
    kernel = np.array([[-0.5, -1, -0.5],
                       [-1, 7, -1],
                       [-0.5, -1, -0.5]]) / 2.0
    sharpened = cv2.filter2D(upscaled, -1, kernel)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def _run_esrgan(image: np.ndarray, session) -> np.ndarray:
    """Run ESRGAN ONNX model for super-resolution."""
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    tensor = rgb.astype(np.float32) / 255.0
    tensor = np.transpose(tensor, (2, 0, 1))  # HWC → CHW
    tensor = np.expand_dims(tensor, 0)

    input_name = session.get_inputs()[0].name
    output = session.run(None, {input_name: tensor})
    result = output[0][0]

    # CHW → HWC
    result = np.transpose(result, (1, 2, 0))
    result = np.clip(result * 255.0, 0, 255).astype(np.uint8)
    return cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
