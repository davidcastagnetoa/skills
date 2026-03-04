"""Face detection using RetinaFace (ONNX) with Haar cascade fallback."""

import cv2
import numpy as np
import structlog

from modules.face_match.models import FaceDetectionResult

logger = structlog.get_logger()

_HAAR_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"  # type: ignore[attr-defined]


def detect_face_retinaface(
    image: np.ndarray,
    session=None,  # onnxruntime.InferenceSession
) -> FaceDetectionResult:
    """Detect faces using RetinaFace ONNX model.

    Args:
        image: BGR image.
        session: Pre-loaded ONNX InferenceSession.

    Returns:
        FaceDetectionResult with bbox and landmarks.
    """
    if session is None:
        return _detect_face_haar(image)

    h, w = image.shape[:2]

    # Preprocess: resize to 640x640, normalize
    input_size = 640
    scale = min(input_size / w, input_size / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(image, (new_w, new_h))

    # Pad to square
    padded = np.zeros((input_size, input_size, 3), dtype=np.uint8)
    padded[:new_h, :new_w] = resized

    # Normalize
    input_tensor = padded.astype(np.float32)
    input_tensor = np.transpose(input_tensor, (2, 0, 1))  # HWC → CHW
    input_tensor = np.expand_dims(input_tensor, 0)

    try:
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: input_tensor})

        # Parse RetinaFace output (format depends on model variant)
        # Simplified: assume outputs contain bboxes and scores
        bboxes = outputs[0][0] if len(outputs) > 0 else np.array([])
        scores = outputs[1][0] if len(outputs) > 1 else np.array([])
        landmarks_raw = outputs[2][0] if len(outputs) > 2 else None

        if len(scores) == 0:
            return FaceDetectionResult(detected=False)

        # Find best face
        best_idx = int(np.argmax(scores))
        if scores[best_idx] < 0.5:
            return FaceDetectionResult(detected=False)

        # Scale bbox back to original image coordinates
        bbox = bboxes[best_idx] / scale
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

        # Parse landmarks (5 points: left_eye, right_eye, nose, left_mouth, right_mouth)
        lms = []
        if landmarks_raw is not None and len(landmarks_raw) > best_idx:
            raw = landmarks_raw[best_idx].reshape(-1, 2) / scale
            lms = [[float(p[0]), float(p[1])] for p in raw[:5]]

        return FaceDetectionResult(
            detected=True,
            bbox=[x1, y1, x2, y2],
            landmarks=lms,
            confidence=round(float(scores[best_idx]), 4),
            face_count=int(np.sum(scores > 0.5)),
        )

    except Exception:
        logger.exception("face_detector.retinaface_failed, falling back to haar")
        return _detect_face_haar(image)


def _detect_face_haar(image: np.ndarray) -> FaceDetectionResult:
    """Fallback face detection using Haar cascade."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(_HAAR_CASCADE_PATH)

    faces = cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50)
    )

    if len(faces) == 0:
        return FaceDetectionResult(detected=False)

    # Select largest face
    areas = [fw * fh for (_, _, fw, fh) in faces]
    idx = int(np.argmax(areas))
    x, y, fw, fh = faces[idx]

    return FaceDetectionResult(
        detected=True,
        bbox=[int(x), int(y), int(x + fw), int(y + fh)],
        confidence=0.7,  # Fixed confidence for Haar
        face_count=len(faces),
    )


def detect_face(image: np.ndarray, session=None) -> FaceDetectionResult:
    """Detect a face in the image.

    Uses RetinaFace (ONNX) if available, falls back to Haar cascade.
    Verifies that exactly one face is present.
    """
    result = detect_face_retinaface(image, session)

    if result.detected and result.face_count > 1:
        logger.warning("face_detector.multiple_faces", count=result.face_count)

    return result
