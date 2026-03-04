"""Face alignment using 5-point landmarks.

Aligns detected faces to a canonical pose for consistent embedding generation.
Standard alignment: eyes horizontal, face centered, cropped to 112x112.
"""

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()

# ArcFace standard reference landmarks for 112x112 aligned face
_REFERENCE_LANDMARKS = np.array(
    [
        [38.2946, 51.6963],   # left eye
        [73.5318, 51.5014],   # right eye
        [56.0252, 71.7366],   # nose tip
        [41.5493, 92.3655],   # left mouth corner
        [70.7299, 92.2041],   # right mouth corner
    ],
    dtype=np.float32,
)

_OUTPUT_SIZE = (112, 112)


def align_face(
    image: np.ndarray,
    landmarks: list[list[float]],
    output_size: tuple[int, int] = _OUTPUT_SIZE,
) -> np.ndarray:
    """Align a face using 5-point landmarks via similarity transform.

    Args:
        image: BGR image containing the face.
        landmarks: 5 landmark points [[x,y], ...] — eyes, nose, mouth corners.
        output_size: Output face crop size (default 112x112 for ArcFace).

    Returns:
        Aligned and cropped face image.
    """
    if len(landmarks) < 5:
        logger.warning("aligner.insufficient_landmarks", count=len(landmarks))
        return _center_crop(image, output_size)

    src_pts = np.array(landmarks[:5], dtype=np.float32)

    # Scale reference landmarks to output size
    ref = _REFERENCE_LANDMARKS.copy()
    if output_size != (112, 112):
        scale_x = output_size[0] / 112.0
        scale_y = output_size[1] / 112.0
        ref[:, 0] *= scale_x
        ref[:, 1] *= scale_y

    # Estimate similarity transform (no shear)
    transform = cv2.estimateAffinePartial2D(src_pts, ref)[0]

    if transform is None:
        logger.warning("aligner.transform_estimation_failed")
        return _center_crop(image, output_size)

    aligned = cv2.warpAffine(
        image, transform, output_size, flags=cv2.INTER_LINEAR
    )

    return aligned


def align_face_from_bbox(
    image: np.ndarray,
    bbox: list[int],
    output_size: tuple[int, int] = _OUTPUT_SIZE,
) -> np.ndarray:
    """Align face using bounding box when landmarks are not available.

    Centers and resizes the face crop.
    """
    x1, y1, x2, y2 = bbox
    h, w = image.shape[:2]

    # Add padding (10%)
    pad_w = int((x2 - x1) * 0.1)
    pad_h = int((y2 - y1) * 0.1)
    x1 = max(0, x1 - pad_w)
    y1 = max(0, y1 - pad_h)
    x2 = min(w, x2 + pad_w)
    y2 = min(h, y2 + pad_h)

    face_crop = image[y1:y2, x1:x2]
    if face_crop.size == 0:
        return np.zeros((*output_size, 3), dtype=np.uint8)

    aligned = cv2.resize(face_crop, output_size)
    return aligned


def _center_crop(image: np.ndarray, output_size: tuple[int, int]) -> np.ndarray:
    """Fallback: center-crop and resize."""
    h, w = image.shape[:2]
    size = min(h, w)
    y_off = (h - size) // 2
    x_off = (w - size) // 2
    cropped = image[y_off:y_off + size, x_off:x_off + size]
    return cv2.resize(cropped, output_size)
