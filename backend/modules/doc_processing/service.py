"""Document processing service — orchestrates the full document analysis pipeline."""

import time

import cv2
import numpy as np
import structlog

from modules.doc_processing.detector import detect_document, extract_document_contour
from modules.doc_processing.enhancer import enhance_document
from modules.doc_processing.face_extractor import extract_face_from_document
from modules.doc_processing.forgery import analyze_forgery
from modules.doc_processing.models import DocumentProcessingResult
from modules.doc_processing.perspective import correct_perspective

logger = structlog.get_logger()


class DocumentProcessorService:
    """Orchestrates all document processing sub-components.

    Pipeline:
        1. Detect document in raw image (contour detection).
        2. Correct perspective (homography).
        3. Enhance image (denoise, CLAHE, sharpen).
        4. Extract face region of the document holder.
        5. Analyze for forgery (ELA, copy-move, EXIF).
    """

    def process(self, image_bytes: bytes) -> DocumentProcessingResult:
        """Process a raw document image through the full pipeline.

        Args:
            image_bytes: Raw image bytes (JPEG/PNG).

        Returns:
            DocumentProcessingResult with processed image, face region, and forgery analysis.
        """
        start = time.perf_counter()

        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return DocumentProcessingResult(
                forgery_score=0.0,
                detected_anomalies=["image_decode_failed"],
                processing_time_ms=0,
            )

        # 1. Detect document
        detection = detect_document(image)
        quality_metrics: dict[str, float] = {
            "detection_confidence": detection.confidence,
        }

        if not detection.detected:
            logger.info("doc_processor.no_document_detected")
            return DocumentProcessingResult(
                detected_anomalies=["no_document_detected"],
                quality_metrics=quality_metrics,
                processing_time_ms=self._elapsed_ms(start),
            )

        # 2. Perspective correction
        corners = extract_document_contour(image)
        corrected = correct_perspective(image, corners=corners)

        # 3. Image enhancement
        enhanced = enhance_document(corrected)

        # Measure quality after enhancement
        gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        brightness = float(np.mean(gray))
        quality_metrics["sharpness"] = round(sharpness, 2)
        quality_metrics["brightness"] = round(brightness, 2)

        # 4. Face region extraction
        face_region = extract_face_from_document(enhanced)
        face_bytes: bytes | None = None
        if face_region is not None:
            _, buf = cv2.imencode(".jpg", face_region, [cv2.IMWRITE_JPEG_QUALITY, 95])
            face_bytes = buf.tobytes()
            quality_metrics["face_extracted"] = 1.0
        else:
            quality_metrics["face_extracted"] = 0.0

        # 5. Forgery analysis
        forgery = analyze_forgery(image, image_bytes)

        # Encode processed image
        _, proc_buf = cv2.imencode(".jpg", enhanced, [cv2.IMWRITE_JPEG_QUALITY, 95])
        processed_bytes = proc_buf.tobytes()

        elapsed = self._elapsed_ms(start)
        logger.info(
            "doc_processor.complete",
            doc_type=detection.document_type,
            forgery_score=forgery.score,
            sharpness=sharpness,
            elapsed_ms=elapsed,
        )

        return DocumentProcessingResult(
            document_type=detection.document_type,
            country=detection.country,
            processed_image=processed_bytes,
            face_region=face_bytes,
            forgery_score=forgery.score,
            detected_anomalies=forgery.anomalies,
            quality_metrics=quality_metrics,
            processing_time_ms=elapsed,
        )

    @staticmethod
    def _elapsed_ms(start: float) -> int:
        return int((time.perf_counter() - start) * 1000)
