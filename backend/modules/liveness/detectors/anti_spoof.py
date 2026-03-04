"""Anti-spoofing model (Silent-Face-Anti-Spoofing / MiniFASNet).

Classifies face images as real or spoof (photo, screen, mask).
Uses ONNX models for inference.
"""

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()

# Model input sizes for MiniFASNet variants
_MODEL_CONFIGS = {
    "2.7_80x80": {"size": (80, 80)},
    "4_0_128x128": {"size": (128, 128)},
}


def preprocess_for_anti_spoof(
    image: np.ndarray,
    target_size: tuple[int, int] = (80, 80),
) -> np.ndarray:
    """Preprocess face image for anti-spoofing model.

    Args:
        image: BGR face crop.
        target_size: Model input size.

    Returns:
        Preprocessed tensor (1, 3, H, W) float32.
    """
    resized = cv2.resize(image, target_size)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = rgb.astype(np.float32) / 255.0
    # Normalize with ImageNet stats
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    normalized = (normalized - mean) / std
    # HWC → CHW → NCHW
    tensor = np.transpose(normalized, (2, 0, 1))
    tensor = np.expand_dims(tensor, axis=0)
    return tensor


def predict_anti_spoof(
    image: np.ndarray,
    session=None,  # onnxruntime.InferenceSession
    target_size: tuple[int, int] = (80, 80),
) -> float:
    """Run anti-spoofing model inference.

    Args:
        image: BGR face crop.
        session: ONNX InferenceSession for the anti-spoofing model.
        target_size: Model input size.

    Returns:
        Score 0-1 (higher = more likely real).
    """
    if session is None:
        logger.debug("anti_spoof.no_model_available")
        return 0.5  # Neutral score when model unavailable

    tensor = preprocess_for_anti_spoof(image, target_size)

    try:
        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: tensor})
        logits = output[0][0]

        # Apply softmax: [spoof_prob, real_prob]
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / exp_logits.sum()

        # Index 1 is typically "real"
        real_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])

        logger.debug("anti_spoof.inference_complete", real_prob=round(real_prob, 4))
        return round(real_prob, 4)

    except Exception:
        logger.exception("anti_spoof.inference_failed")
        return 0.5


def analyze_anti_spoof(
    frames: list[np.ndarray],
    session=None,
    session_large=None,
) -> float:
    """Run anti-spoofing analysis on multiple frames.

    Uses two model scales when available (80x80 and 128x128) and
    averages predictions for robustness.

    Args:
        frames: List of BGR face crops.
        session: ONNX session for the 80x80 model.
        session_large: ONNX session for the 128x128 model.

    Returns:
        Score 0-1 (higher = more likely real).
    """
    if not frames:
        return 0.0

    scores: list[float] = []
    for frame in frames[:5]:
        # Small model
        s1 = predict_anti_spoof(frame, session, (80, 80))
        scores.append(s1)

        # Large model (if available)
        if session_large is not None:
            s2 = predict_anti_spoof(frame, session_large, (128, 128))
            scores.append(s2)

    avg_score = float(np.mean(scores)) if scores else 0.0

    logger.debug(
        "anti_spoof.analysis_complete",
        n_frames=len(frames),
        n_scores=len(scores),
        avg_score=round(avg_score, 4),
    )

    return round(avg_score, 4)
