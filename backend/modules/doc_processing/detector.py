"""Document detection: find and classify the document in a raw image."""

import cv2
import numpy as np
import structlog

from modules.doc_processing.models import BoundingBox, DocumentDetection

logger = structlog.get_logger()

# Minimum area ratio of document relative to the full image
_MIN_AREA_RATIO = 0.10
# Approximation accuracy for contour polygon
_APPROX_EPS = 0.02


def detect_document(image: np.ndarray) -> DocumentDetection:
    """Detect the largest rectangular region in the image.

    Uses Canny edge detection + contour finding to locate the document.
    Returns bounding box and detection confidence.
    """
    h, w = image.shape[:2]
    total_area = h * w

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # Dilate to close gaps in edges
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_contour = None
    best_area = 0.0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < total_area * _MIN_AREA_RATIO:
            continue

        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, _APPROX_EPS * peri, True)

        # A document should approximate to a quadrilateral
        if len(approx) == 4 and area > best_area:
            best_contour = approx
            best_area = area

    if best_contour is None:
        logger.debug("document_detector.no_quadrilateral_found")
        return DocumentDetection(detected=False)

    x, y, bw, bh = cv2.boundingRect(best_contour)
    confidence = min(best_area / total_area, 1.0)

    return DocumentDetection(
        detected=True,
        bounding_box=BoundingBox(x1=x, y1=y, x2=x + bw, y2=y + bh),
        confidence=round(confidence, 3),
    )


def order_corner_points(pts: np.ndarray) -> np.ndarray:
    """Order 4 corner points as: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]      # top-left
    rect[2] = pts[np.argmax(s)]      # bottom-right
    rect[1] = pts[np.argmin(d)]      # top-right
    rect[3] = pts[np.argmax(d)]      # bottom-left
    return rect


def extract_document_contour(image: np.ndarray) -> np.ndarray | None:
    """Return the 4 corner points of the document, or None if not found."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = image.shape[:2]
    min_area = h * w * _MIN_AREA_RATIO

    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        area = cv2.contourArea(contour)
        if area < min_area:
            break
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, _APPROX_EPS * peri, True)
        if len(approx) == 4:
            return order_corner_points(approx.reshape(4, 2))

    return None
