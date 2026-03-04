"""Depth estimation for liveness detection.

Uses MiDaS v2.1 small (ONNX) for monocular depth estimation.
Real faces show 3D depth variation; flat photos/screens are nearly uniform.
"""

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()

# Expected input size for MiDaS v2.1 small
_MIDAS_INPUT_SIZE = (256, 256)


def estimate_depth_from_model(
    image: np.ndarray,
    session=None,  # onnxruntime.InferenceSession
) -> np.ndarray | None:
    """Run MiDaS depth estimation model.

    Args:
        image: BGR face image.
        session: Pre-loaded ONNX InferenceSession for MiDaS.

    Returns:
        Depth map (float32 HxW) or None if model not available.
    """
    if session is None:
        return None

    # Preprocess
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, _MIDAS_INPUT_SIZE)
    input_tensor = resized.astype(np.float32) / 255.0
    input_tensor = np.transpose(input_tensor, (2, 0, 1))  # HWC → CHW
    input_tensor = np.expand_dims(input_tensor, axis=0)  # Add batch dim

    try:
        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: input_tensor})
        depth_map = output[0].squeeze()
        return depth_map.astype(np.float32)
    except Exception:
        logger.exception("depth.model_inference_failed")
        return None


def analyze_depth_variation(depth_map: np.ndarray) -> float:
    """Analyze depth map for 3D face characteristics.

    Real faces have significant depth variation (nose protrudes, eyes recede).
    Flat photos/screens have minimal variation.

    Returns:
        Score 0-1 (higher = more likely real 3D face).
    """
    if depth_map is None or depth_map.size == 0:
        return 0.0

    # Normalize depth map to 0-1
    d_min, d_max = depth_map.min(), depth_map.max()
    if d_max - d_min < 1e-6:
        return 0.0  # Completely flat → likely a photo

    normalized = (depth_map - d_min) / (d_max - d_min)

    # Metrics for 3D-ness
    std_dev = float(np.std(normalized))
    # A real face has std > 0.1 typically
    depth_range = float(d_max - d_min)

    # Gradient magnitude (edges in depth = 3D structure)
    grad_x = cv2.Sobel(normalized, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(normalized, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    avg_gradient = float(np.mean(grad_mag))

    # Combine features into a score
    # Higher std and gradient → more likely a real 3D face
    score = min(std_dev * 3.0 + avg_gradient * 2.0, 1.0)

    logger.debug(
        "depth.analysis_complete",
        std_dev=round(std_dev, 4),
        avg_gradient=round(avg_gradient, 4),
        score=round(score, 4),
    )

    return round(max(score, 0.0), 4)


def estimate_depth(image: np.ndarray, session=None) -> float:
    """Full depth-based liveness check.

    If model is available, uses MiDaS. Otherwise falls back to
    Laplacian-based pseudo-depth estimation.

    Returns:
        Score 0-1 (higher = more likely real).
    """
    # Try model-based depth
    depth_map = estimate_depth_from_model(image, session)
    if depth_map is not None:
        return analyze_depth_variation(depth_map)

    # Fallback: Laplacian variance as proxy for 3D structure
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = float(laplacian.var())

    # Normalize: real faces typically have Laplacian variance > 100
    score = min(variance / 500.0, 1.0)

    logger.debug("depth.fallback_laplacian", variance=round(variance, 2), score=round(score, 4))
    return round(score, 4)
