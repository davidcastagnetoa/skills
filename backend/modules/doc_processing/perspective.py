"""Perspective correction via homography transform."""

import cv2
import numpy as np
import structlog

from modules.doc_processing.detector import extract_document_contour, order_corner_points

logger = structlog.get_logger()

# Standard output sizes by document type (width x height)
STANDARD_SIZES: dict[str, tuple[int, int]] = {
    "DNI": (856, 540),       # ID-1 format (credit card size) at 100 DPI
    "PASSPORT": (890, 625),  # ID-3 format at 100 DPI
    "LICENSE": (856, 540),   # ID-1 format
    "DEFAULT": (800, 500),
}


def correct_perspective(
    image: np.ndarray,
    corners: np.ndarray | None = None,
    doc_type: str = "DEFAULT",
) -> np.ndarray:
    """Apply perspective correction to extract a flat, front-facing document.

    Args:
        image: Source image (BGR).
        corners: 4 corner points [TL, TR, BR, BL]. Auto-detected if None.
        doc_type: Document type for choosing output size.

    Returns:
        Warped image with corrected perspective.
    """
    if corners is None:
        corners = extract_document_contour(image)

    if corners is None:
        logger.debug("perspective.no_corners_found, returning crop")
        return image

    src_pts = corners.astype(np.float32)

    out_w, out_h = STANDARD_SIZES.get(doc_type, STANDARD_SIZES["DEFAULT"])
    dst_pts = np.array(
        [[0, 0], [out_w - 1, 0], [out_w - 1, out_h - 1], [0, out_h - 1]],
        dtype=np.float32,
    )

    matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(image, matrix, (out_w, out_h), flags=cv2.INTER_CUBIC)

    logger.debug("perspective.corrected", doc_type=doc_type, output_size=(out_w, out_h))
    return warped
