"""Extract the face region from a document image."""

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()

# Cascade classifier for face detection on documents (lightweight, no GPU needed)
_FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"  # type: ignore[attr-defined]


def extract_face_from_document(image: np.ndarray, min_face_ratio: float = 0.03) -> np.ndarray | None:
    """Locate and extract the face photo from a document image.

    Uses Haar cascade as a lightweight detector (works well for passport/ID photos
    which are front-facing, well-lit, and standardized).

    Args:
        image: Document image (BGR), already perspective-corrected.
        min_face_ratio: Minimum face area as ratio of image area.

    Returns:
        Cropped face region (BGR) or None if no face found.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    min_size = int(min(h, w) * 0.1)

    cascade = cv2.CascadeClassifier(_FACE_CASCADE_PATH)
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(min_size, min_size),
    )

    if len(faces) == 0:
        logger.debug("face_extractor.no_face_found_in_document")
        return None

    # Pick the largest face (the holder's photo, not holograms/stamps)
    areas = [fw * fh for (_, _, fw, fh) in faces]
    idx = int(np.argmax(areas))
    fx, fy, fw, fh = faces[idx]

    # Check minimum size
    face_area = fw * fh
    image_area = h * w
    if face_area / image_area < min_face_ratio:
        logger.debug("face_extractor.face_too_small", ratio=face_area / image_area)
        return None

    # Add padding (20%) for alignment downstream
    pad_x = int(fw * 0.2)
    pad_y = int(fh * 0.2)
    x1 = max(0, fx - pad_x)
    y1 = max(0, fy - pad_y)
    x2 = min(w, fx + fw + pad_x)
    y2 = min(h, fy + fh + pad_y)

    face_crop = image[y1:y2, x1:x2]
    logger.debug("face_extractor.extracted", size=(x2 - x1, y2 - y1))
    return face_crop
