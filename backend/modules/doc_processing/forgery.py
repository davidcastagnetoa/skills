"""Forgery and manipulation detection for document images."""

import io

import cv2
import numpy as np
import structlog
from PIL import Image

from modules.doc_processing.models import ForgeryAnalysis

logger = structlog.get_logger()


def error_level_analysis(image: np.ndarray, quality: int = 90, scale: float = 15.0) -> tuple[float, np.ndarray]:
    """Perform Error Level Analysis (ELA).

    Re-saves the image at a fixed JPEG quality and computes the difference.
    Tampered regions show higher error levels than the rest of the image.

    Returns:
        (ela_score, ela_image) where score is 0-1 (higher = more suspicious).
    """
    # Convert to PIL for JPEG resave
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    resaved = np.array(Image.open(buffer))

    # Compute absolute difference
    original_float = rgb.astype(np.float32)
    resaved_float = resaved.astype(np.float32)
    diff = np.abs(original_float - resaved_float)

    # Scale for visibility
    ela_image = np.clip(diff * scale, 0, 255).astype(np.uint8)

    # Score: mean of the brightest 5% of pixels (potential tampering regions)
    gray_diff = cv2.cvtColor(ela_image, cv2.COLOR_RGB2GRAY)
    flat = gray_diff.flatten()
    top_k = int(len(flat) * 0.05)
    if top_k == 0:
        return 0.0, ela_image
    top_values = np.partition(flat, -top_k)[-top_k:]
    score = float(np.mean(top_values) / 255.0)

    return round(score, 4), cv2.cvtColor(ela_image, cv2.COLOR_RGB2BGR)


def copy_move_detection(image: np.ndarray, block_size: int = 16, threshold: float = 0.95) -> float:
    """Detect copy-move forgery using block matching.

    Divides the image into blocks and finds highly similar non-adjacent blocks,
    which may indicate cloned regions.

    Returns:
        Score 0-1 (higher = more likely copy-move forgery detected).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    blocks_y = h // block_size
    blocks_x = w // block_size

    if blocks_y < 2 or blocks_x < 2:
        return 0.0

    # Extract DCT features from each block
    features = []
    positions = []
    for by in range(blocks_y):
        for bx in range(blocks_x):
            block = gray[by * block_size:(by + 1) * block_size, bx * block_size:(bx + 1) * block_size]
            dct_block = cv2.dct(block.astype(np.float32))
            # Use top-left 4x4 DCT coefficients as feature
            feat = dct_block[:4, :4].flatten()
            norm = np.linalg.norm(feat)
            if norm > 0:
                feat = feat / norm
            features.append(feat)
            positions.append((bx, by))

    if len(features) < 2:
        return 0.0

    features_arr = np.array(features)
    # Compute similarity matrix (dot product of normalized features)
    similarity = features_arr @ features_arr.T

    suspicious_pairs = 0
    total_comparisons = 0

    for i in range(len(features)):
        for j in range(i + 1, len(features)):
            bx_i, by_i = positions[i]
            bx_j, by_j = positions[j]
            # Skip adjacent blocks
            if abs(bx_i - bx_j) <= 1 and abs(by_i - by_j) <= 1:
                continue
            total_comparisons += 1
            if similarity[i, j] > threshold:
                suspicious_pairs += 1

    if total_comparisons == 0:
        return 0.0

    score = min(suspicious_pairs / max(total_comparisons * 0.001, 1), 1.0)
    return round(score, 4)


def check_exif_metadata(image_bytes: bytes) -> tuple[bool, list[str]]:
    """Check EXIF metadata for signs of editing.

    Returns:
        (is_suspicious, list_of_findings).
    """
    findings: list[str] = []

    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        exif_data = pil_img.getexif()

        if not exif_data:
            return False, []

        # Check for editing software
        software_tag = 305
        if software_tag in exif_data:
            sw = str(exif_data[software_tag]).lower()
            suspicious_software = ["photoshop", "gimp", "paint", "affinity", "pixelmator", "snapseed"]
            for tool in suspicious_software:
                if tool in sw:
                    findings.append(f"editing_software_detected:{exif_data[software_tag]}")

        # Check for modification date different from creation
        date_original = exif_data.get(36867)  # DateTimeOriginal
        date_modified = exif_data.get(306)    # DateTime
        if date_original and date_modified and str(date_original) != str(date_modified):
            findings.append("modification_date_differs_from_original")

    except Exception:
        pass

    return len(findings) > 0, findings


def analyze_forgery(image: np.ndarray, image_bytes: bytes) -> ForgeryAnalysis:
    """Run all forgery detection methods and aggregate results.

    Args:
        image: Document image as numpy array (BGR).
        image_bytes: Original image bytes (for EXIF analysis).

    Returns:
        ForgeryAnalysis with per-method scores and aggregate score.
    """
    anomalies: list[str] = []

    # ELA
    ela_score, _ = error_level_analysis(image)
    if ela_score > 0.4:
        anomalies.append("ela_tampering_suspected")

    # Copy-move
    cm_score = copy_move_detection(image)
    if cm_score > 0.3:
        anomalies.append("copy_move_forgery_suspected")

    # EXIF
    exif_suspicious, exif_findings = check_exif_metadata(image_bytes)
    if exif_suspicious:
        anomalies.extend(exif_findings)

    # Aggregate score (weighted)
    aggregate = (ela_score * 0.4) + (cm_score * 0.3) + (float(exif_suspicious) * 0.3)

    logger.debug(
        "forgery.analysis_complete",
        ela=ela_score,
        copy_move=cm_score,
        exif_suspicious=exif_suspicious,
        aggregate=round(aggregate, 4),
    )

    return ForgeryAnalysis(
        score=round(min(aggregate, 1.0), 4),
        anomalies=anomalies,
        ela_score=ela_score,
        copy_move_score=cm_score,
        exif_suspicious=exif_suspicious,
    )
