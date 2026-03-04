"""Celery tasks for ML pipeline modules.

Each module is registered as a Celery task with:
- Specific queue assignment (cpu/gpu)
- Per-task timeouts
- Retry with exponential backoff for transient failures
"""

import structlog

from infrastructure.celery_app import celery_app

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Document Processing (CPU-bound, no GPU needed)
# ---------------------------------------------------------------------------


@celery_app.task(
    name="ml.process_document",
    queue="cpu",
    bind=True,
    max_retries=2,
    soft_time_limit=5,
    time_limit=8,
)
def process_document(self, session_id: str, image_data: bytes) -> dict:
    """Process a document image through the full pipeline.

    Queue: cpu (OpenCV operations, no GPU needed)
    Timeout: 5s soft / 8s hard
    """
    try:
        from modules.doc_processing.service import DocumentProcessorService

        logger.info("task.process_document.start", session_id=session_id)
        service = DocumentProcessorService()
        result = service.process(image_data)

        return result.model_dump(exclude={"processed_image", "face_region"}) | {
            "session_id": session_id,
            "has_processed_image": result.processed_image is not None,
            "has_face_region": result.face_region is not None,
        }

    except Exception as exc:
        logger.error("task.process_document.failed", session_id=session_id, error=str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


# ---------------------------------------------------------------------------
# OCR (CPU-bound)
# ---------------------------------------------------------------------------


@celery_app.task(
    name="ml.run_ocr",
    queue="cpu",
    bind=True,
    max_retries=2,
    soft_time_limit=5,
    time_limit=8,
)
def run_ocr(self, session_id: str, doc_image_data: bytes) -> dict:
    """Extract text and MRZ from a processed document image.

    Queue: cpu (PaddleOCR/EasyOCR/Tesseract)
    Timeout: 5s soft / 8s hard
    """
    try:
        from modules.ocr.service import OCRService

        logger.info("task.run_ocr.start", session_id=session_id)
        service = OCRService()
        result = service.extract(doc_image_data)

        return result.model_dump() | {"session_id": session_id}

    except Exception as exc:
        logger.error("task.run_ocr.failed", session_id=session_id, error=str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


# ---------------------------------------------------------------------------
# Liveness Detection (GPU-bound for anti-spoof/deepfake models)
# ---------------------------------------------------------------------------


@celery_app.task(
    name="ml.run_liveness",
    queue="gpu",
    bind=True,
    max_retries=2,
    soft_time_limit=3,
    time_limit=5,
)
def run_liveness(self, session_id: str, frames_data: list[bytes]) -> dict:
    """Run liveness detection on a sequence of selfie frames.

    Queue: gpu (anti-spoofing and deepfake models use GPU)
    Timeout: 3s soft / 5s hard
    """
    try:
        import cv2
        import numpy as np

        from modules.liveness.service import LivenessService

        logger.info("task.run_liveness.start", session_id=session_id, n_frames=len(frames_data))

        # Decode frames
        frames = []
        for frame_bytes in frames_data:
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                frames.append(frame)

        if not frames:
            return {
                "session_id": session_id,
                "is_live": False,
                "liveness_score": 0.0,
                "error": "no_valid_frames",
            }

        service = LivenessService()
        result = service.analyze(frames)

        return result.model_dump() | {"session_id": session_id}

    except Exception as exc:
        logger.error("task.run_liveness.failed", session_id=session_id, error=str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


# ---------------------------------------------------------------------------
# Face Match (GPU-bound for ArcFace embedding generation)
# ---------------------------------------------------------------------------


@celery_app.task(
    name="ml.run_face_match",
    queue="gpu",
    bind=True,
    max_retries=2,
    soft_time_limit=3,
    time_limit=5,
)
def run_face_match(self, session_id: str, selfie_data: bytes, doc_face_data: bytes) -> dict:
    """Compare selfie with document face.

    Queue: gpu (ArcFace model uses GPU)
    Timeout: 3s soft / 5s hard
    """
    try:
        from modules.face_match.service import FaceMatchService

        logger.info("task.run_face_match.start", session_id=session_id)
        service = FaceMatchService()
        result = service.compare(selfie_data, doc_face_data)

        return result.model_dump() | {"session_id": session_id}

    except Exception as exc:
        logger.error("task.run_face_match.failed", session_id=session_id, error=str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
