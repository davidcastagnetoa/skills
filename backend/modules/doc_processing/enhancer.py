"""Image enhancement: denoising, CLAHE, sharpening."""

import cv2
import numpy as np


def denoise(image: np.ndarray, strength: int = 10) -> np.ndarray:
    """Apply Non-Local Means denoising while preserving edges."""
    return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)


def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, grid_size: int = 8) -> np.ndarray:
    """Apply Contrast Limited Adaptive Histogram Equalization."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(grid_size, grid_size))
    l_channel = clahe.apply(l_channel)
    merged = cv2.merge([l_channel, a_channel, b_channel])
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def sharpen(image: np.ndarray, amount: float = 1.0) -> np.ndarray:
    """Apply unsharp mask sharpening.

    Args:
        image: Input BGR image.
        amount: Sharpening strength (1.0 = moderate).
    """
    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=3)
    sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
    return sharpened


def enhance_document(image: np.ndarray) -> np.ndarray:
    """Full enhancement pipeline for a document image.

    1. Denoise (remove sensor/compression noise).
    2. CLAHE (normalize contrast, handle uneven lighting).
    3. Sharpen (improve text readability).
    """
    result = denoise(image, strength=8)
    result = apply_clahe(result, clip_limit=2.0)
    result = sharpen(result, amount=0.8)
    return result
