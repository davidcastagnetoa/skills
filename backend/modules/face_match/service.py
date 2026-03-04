"""Face match service — orchestrates detection, alignment, embedding, and comparison."""

import time

import cv2
import numpy as np
import structlog

from modules.face_match.aligner import align_face, align_face_from_bbox
from modules.face_match.detector import detect_face
from modules.face_match.embeddings import cosine_similarity, generate_embedding
from modules.face_match.models import FaceMatchResult, MatchDecision
from modules.face_match.quality import apply_super_resolution, assess_quality

logger = structlog.get_logger()

# Decision thresholds (configurable)
_MATCH_THRESHOLD = 0.85
_REVIEW_THRESHOLD = 0.70
_QUALITY_SR_THRESHOLD = 0.5  # Apply super-resolution below this quality


class FaceMatchService:
    """Orchestrates the full face comparison pipeline.

    Pipeline:
        1. Detect face in selfie and document.
        2. Assess quality; apply super-resolution to document face if needed.
        3. Align both faces (5-point landmark alignment).
        4. Generate embeddings (ArcFace primary, FaceNet backup).
        5. Compute cosine similarity.
        6. Decide: MATCH / REVIEW / NO_MATCH.
    """

    def __init__(
        self,
        face_detector_session=None,
        arcface_session=None,
        facenet_session=None,
        esrgan_session=None,
        match_threshold: float = _MATCH_THRESHOLD,
        review_threshold: float = _REVIEW_THRESHOLD,
    ) -> None:
        self._detector_session = face_detector_session
        self._arcface_session = arcface_session
        self._facenet_session = facenet_session
        self._esrgan_session = esrgan_session
        self._match_threshold = match_threshold
        self._review_threshold = review_threshold

    def compare(self, selfie_bytes: bytes, document_face_bytes: bytes) -> FaceMatchResult:
        """Compare a selfie with a document face image.

        Args:
            selfie_bytes: JPEG/PNG bytes of the selfie.
            document_face_bytes: JPEG/PNG bytes of the extracted document face.

        Returns:
            FaceMatchResult with similarity score and decision.
        """
        start = time.perf_counter()

        # Decode images
        selfie_img = self._decode(selfie_bytes)
        doc_img = self._decode(document_face_bytes)

        if selfie_img is None or doc_img is None:
            return FaceMatchResult(
                processing_time_ms=self._elapsed_ms(start),
            )

        # 1. Detect faces
        selfie_det = detect_face(selfie_img, self._detector_session)
        doc_det = detect_face(doc_img, self._detector_session)

        if not selfie_det.detected:
            logger.warning("face_match.no_face_in_selfie")
            return FaceMatchResult(processing_time_ms=self._elapsed_ms(start))

        if not doc_det.detected:
            logger.warning("face_match.no_face_in_document")
            return FaceMatchResult(processing_time_ms=self._elapsed_ms(start))

        # 2. Assess quality
        selfie_crop = self._crop_face(selfie_img, selfie_det.bbox)
        doc_crop = self._crop_face(doc_img, doc_det.bbox)

        selfie_quality = assess_quality(selfie_crop)
        doc_quality = assess_quality(doc_crop)

        # Super-resolution on document face if quality is low
        sr_applied = False
        if doc_quality.score < _QUALITY_SR_THRESHOLD:
            doc_crop = apply_super_resolution(doc_crop, self._esrgan_session)
            doc_quality = assess_quality(doc_crop)
            sr_applied = True
            logger.info("face_match.super_resolution_applied", new_quality=doc_quality.score)

        # 3. Align faces
        if selfie_det.landmarks:
            selfie_aligned = align_face(selfie_img, selfie_det.landmarks)
        else:
            selfie_aligned = align_face_from_bbox(selfie_img, selfie_det.bbox)

        if doc_det.landmarks:
            doc_aligned = align_face(doc_img, doc_det.landmarks)
        else:
            doc_aligned = align_face_from_bbox(doc_img, doc_det.bbox)

        # 4. Generate embeddings
        selfie_emb = generate_embedding(
            selfie_aligned, self._arcface_session, self._facenet_session
        )
        doc_emb = generate_embedding(
            doc_aligned, self._arcface_session, self._facenet_session
        )

        if selfie_emb is None or doc_emb is None:
            logger.warning("face_match.embedding_generation_failed")
            return FaceMatchResult(
                selfie_quality=selfie_quality,
                document_quality=doc_quality,
                super_resolution_applied=sr_applied,
                processing_time_ms=self._elapsed_ms(start),
            )

        # 5. Compute similarity
        similarity = cosine_similarity(selfie_emb, doc_emb)
        # Clamp to [0, 1] for face matching context
        similarity = max(0.0, similarity)

        # 6. Decision
        if similarity >= self._match_threshold:
            decision = MatchDecision.MATCH
        elif similarity >= self._review_threshold:
            decision = MatchDecision.REVIEW
        else:
            decision = MatchDecision.NO_MATCH

        # Confidence: how far from the review zone boundary
        if decision == MatchDecision.MATCH:
            confidence = min((similarity - self._match_threshold) / 0.15 + 0.8, 1.0)
        elif decision == MatchDecision.NO_MATCH:
            confidence = min((self._review_threshold - similarity) / 0.30 + 0.7, 1.0)
        else:
            confidence = 0.5  # In the review zone — uncertain

        elapsed = self._elapsed_ms(start)

        logger.info(
            "face_match.complete",
            similarity=round(similarity, 4),
            decision=decision.value,
            confidence=round(confidence, 4),
            sr_applied=sr_applied,
            elapsed_ms=elapsed,
        )

        return FaceMatchResult(
            decision=decision,
            similarity_score=round(similarity, 4),
            confidence=round(confidence, 4),
            selfie_quality=selfie_quality,
            document_quality=doc_quality,
            super_resolution_applied=sr_applied,
            processing_time_ms=elapsed,
        )

    @staticmethod
    def _decode(image_bytes: bytes) -> np.ndarray | None:
        """Decode image bytes to numpy array."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image

    @staticmethod
    def _crop_face(image: np.ndarray, bbox: list[int]) -> np.ndarray:
        """Crop face region from image using bounding box."""
        if not bbox or len(bbox) < 4:
            return image
        x1, y1, x2, y2 = bbox
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        return image[y1:y2, x1:x2]

    @staticmethod
    def _elapsed_ms(start: float) -> int:
        return int((time.perf_counter() - start) * 1000)
