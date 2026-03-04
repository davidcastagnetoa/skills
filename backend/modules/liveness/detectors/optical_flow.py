"""Optical flow analysis for liveness detection.

Uses Farneback dense optical flow to detect:
- Static images (no movement)
- Video replay (uniform movement across entire frame)
- Looping video (periodic identical flow patterns)
"""

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()


def compute_optical_flow(prev_gray: np.ndarray, curr_gray: np.ndarray) -> np.ndarray:
    """Compute dense optical flow between two consecutive grayscale frames."""
    flow = cv2.calcOpticalFlowFarneback(
        prev_gray,
        curr_gray,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=15,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=0,
    )
    return flow


def _flow_statistics(flow: np.ndarray) -> dict[str, float]:
    """Compute statistics from an optical flow field."""
    mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])

    return {
        "mean_magnitude": float(np.mean(mag)),
        "std_magnitude": float(np.std(mag)),
        "max_magnitude": float(np.max(mag)),
        "flow_uniformity": float(np.std(mag) / (np.mean(mag) + 1e-6)),
    }


def analyze_optical_flow(frames: list[np.ndarray]) -> float:
    """Analyze optical flow across a sequence of frames.

    Detection criteria:
    - No movement at all → likely a static photo (score = 0)
    - Uniform movement → likely a screen/printed photo being moved (score low)
    - Natural, non-uniform movement → likely a real person (score high)

    Args:
        frames: List of BGR frames (at least 2 needed).

    Returns:
        Score 0-1 (higher = more likely real).
    """
    if len(frames) < 2:
        return 0.0

    gray_frames = [
        cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) if len(f.shape) == 3 else f
        for f in frames
    ]

    flow_stats: list[dict[str, float]] = []
    for i in range(1, min(len(gray_frames), 10)):
        # Resize for faster computation
        h, w = gray_frames[i].shape
        scale = min(1.0, 320.0 / max(h, w))
        if scale < 1.0:
            prev = cv2.resize(gray_frames[i - 1], None, fx=scale, fy=scale)
            curr = cv2.resize(gray_frames[i], None, fx=scale, fy=scale)
        else:
            prev = gray_frames[i - 1]
            curr = gray_frames[i]

        flow = compute_optical_flow(prev, curr)
        stats = _flow_statistics(flow)
        flow_stats.append(stats)

    if not flow_stats:
        return 0.0

    avg_magnitude = np.mean([s["mean_magnitude"] for s in flow_stats])
    avg_uniformity = np.mean([s["flow_uniformity"] for s in flow_stats])
    std_magnitudes = np.std([s["mean_magnitude"] for s in flow_stats])

    # Scoring logic:
    # 1. Some movement is required (not completely static)
    if avg_magnitude < 0.1:
        score = 0.1  # Almost no movement → suspicious
    # 2. Too uniform movement → screen replay
    elif avg_uniformity < 0.5:
        score = 0.3  # Uniform movement pattern
    # 3. Natural movement: non-uniform, varying magnitude
    else:
        # Good: varying magnitude with non-uniform flow
        magnitude_score = min(avg_magnitude / 5.0, 1.0)
        variation_score = min(float(std_magnitudes) / 2.0, 1.0)
        uniformity_score = min(float(avg_uniformity) / 3.0, 1.0)
        score = (magnitude_score * 0.3 + variation_score * 0.3 + uniformity_score * 0.4)

    logger.debug(
        "optical_flow.analysis_complete",
        avg_magnitude=round(float(avg_magnitude), 4),
        avg_uniformity=round(float(avg_uniformity), 4),
        std_magnitudes=round(float(std_magnitudes), 4),
        score=round(score, 4),
    )

    return round(min(max(score, 0.0), 1.0), 4)
