"""Micro-texture analysis for liveness detection.

Uses Local Binary Patterns (LBP) and Fourier frequency analysis to detect
textures characteristic of printed photos or screen displays.
"""

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()


def _compute_lbp(gray: np.ndarray, radius: int = 1, n_points: int = 8) -> np.ndarray:
    """Compute Local Binary Pattern for the given grayscale image.

    A simplified uniform LBP implementation.
    """
    h, w = gray.shape
    lbp = np.zeros((h - 2 * radius, w - 2 * radius), dtype=np.uint8)

    for i in range(n_points):
        angle = 2.0 * np.pi * i / n_points
        dx = int(round(radius * np.cos(angle)))
        dy = int(round(-radius * np.sin(angle)))

        # Shifted neighbor
        y_start = radius + dy
        x_start = radius + dx
        neighbor = gray[y_start:y_start + lbp.shape[0], x_start:x_start + lbp.shape[1]]
        center = gray[radius:radius + lbp.shape[0], radius:radius + lbp.shape[1]]

        lbp |= ((neighbor >= center).astype(np.uint8) << i)

    return lbp


def _lbp_histogram(lbp: np.ndarray, n_bins: int = 256) -> np.ndarray:
    """Compute normalized histogram of LBP values."""
    hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins))
    hist = hist.astype(np.float64)
    total = hist.sum()
    if total > 0:
        hist /= total
    return hist


def _fourier_high_freq_ratio(gray: np.ndarray) -> float:
    """Compute ratio of high-frequency energy in the Fourier spectrum.

    Printed photos and screens tend to have less high-frequency detail
    than real skin.
    """
    f_transform = np.fft.fft2(gray.astype(np.float32))
    f_shift = np.fft.fftshift(f_transform)
    magnitude = np.abs(f_shift)

    h, w = magnitude.shape
    cy, cx = h // 2, w // 2

    # Define a radius for "low frequency" region (center 20%)
    radius = int(min(h, w) * 0.1)
    y, x = np.ogrid[:h, :w]
    mask_low = ((x - cx) ** 2 + (y - cy) ** 2) <= radius ** 2

    total_energy = magnitude.sum()
    if total_energy == 0:
        return 0.0

    low_freq_energy = magnitude[mask_low].sum()
    high_freq_energy = total_energy - low_freq_energy

    return float(high_freq_energy / total_energy)


def analyze_texture(frames: list[np.ndarray]) -> float:
    """Analyze micro-texture across frames for liveness.

    Computes LBP texture features and Fourier frequency analysis.
    Real skin has more micro-texture variation than paper or screens.

    Args:
        frames: List of BGR face crops.

    Returns:
        Score 0-1 (higher = more likely real).
    """
    if not frames:
        return 0.0

    lbp_scores: list[float] = []
    fourier_scores: list[float] = []

    for frame in frames[:5]:  # Analyze up to 5 frames
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame

        # LBP analysis
        lbp = _compute_lbp(gray)
        hist = _lbp_histogram(lbp)
        # Real faces have more uniform LBP distribution (more diverse texture)
        # Entropy as a proxy for texture diversity
        nonzero = hist[hist > 0]
        entropy = -np.sum(nonzero * np.log2(nonzero))
        # Normalize: max entropy for 256 bins is 8
        lbp_score = min(entropy / 6.0, 1.0)
        lbp_scores.append(lbp_score)

        # Fourier analysis
        high_ratio = _fourier_high_freq_ratio(gray)
        fourier_scores.append(high_ratio)

    avg_lbp = np.mean(lbp_scores) if lbp_scores else 0.0
    avg_fourier = np.mean(fourier_scores) if fourier_scores else 0.0

    # Combined score (weighted)
    score = float(avg_lbp * 0.5 + avg_fourier * 0.5)

    logger.debug(
        "texture.analysis_complete",
        lbp_score=round(float(avg_lbp), 4),
        fourier_score=round(float(avg_fourier), 4),
        combined=round(score, 4),
    )

    return round(min(max(score, 0.0), 1.0), 4)
