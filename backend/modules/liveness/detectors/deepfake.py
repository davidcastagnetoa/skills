"""Deepfake detection using XceptionNet (FaceForensics++).

Detects GAN-generated faces, face swaps, and face reenactment artifacts.
"""

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()

# XceptionNet input size
_INPUT_SIZE = (299, 299)


def preprocess_for_xception(image: np.ndarray) -> np.ndarray:
    """Preprocess face image for XceptionNet.

    Args:
        image: BGR face crop.

    Returns:
        Preprocessed tensor (1, 3, 299, 299) float32.
    """
    resized = cv2.resize(image, _INPUT_SIZE)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = rgb.astype(np.float32) / 255.0
    # XceptionNet normalization
    normalized = (normalized - 0.5) / 0.5
    tensor = np.transpose(normalized, (2, 0, 1))  # HWC → CHW
    tensor = np.expand_dims(tensor, axis=0)
    return tensor


def predict_deepfake(
    image: np.ndarray,
    session=None,  # onnxruntime.InferenceSession
) -> float:
    """Run deepfake detection model.

    Args:
        image: BGR face crop.
        session: ONNX InferenceSession for XceptionNet.

    Returns:
        Score 0-1 (higher = more likely real / not a deepfake).
    """
    if session is None:
        return 0.5  # Neutral when model not available

    tensor = preprocess_for_xception(image)

    try:
        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: tensor})
        logits = output[0][0]

        # Apply sigmoid for binary classification (real vs fake)
        if len(logits) == 1:
            prob_real = float(1 / (1 + np.exp(-logits[0])))
        else:
            # Softmax for multi-class
            exp_logits = np.exp(logits - np.max(logits))
            probs = exp_logits / exp_logits.sum()
            prob_real = float(probs[0])  # Index 0 = real

        logger.debug("deepfake.inference_complete", prob_real=round(prob_real, 4))
        return round(prob_real, 4)

    except Exception:
        logger.exception("deepfake.inference_failed")
        return 0.5


def analyze_deepfake(frames: list[np.ndarray], session=None) -> float:
    """Analyze multiple frames for deepfake artifacts.

    Args:
        frames: List of BGR face crops.
        session: ONNX InferenceSession for XceptionNet.

    Returns:
        Score 0-1 (higher = more likely real).
    """
    if not frames:
        return 0.0

    scores = [predict_deepfake(f, session) for f in frames[:5]]
    avg = float(np.mean(scores)) if scores else 0.0

    logger.debug("deepfake.analysis_complete", avg_score=round(avg, 4))
    return round(avg, 4)
