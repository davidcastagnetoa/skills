"""Unit tests for the face match module."""

import cv2
import numpy as np
import pytest

from modules.face_match.aligner import align_face, align_face_from_bbox, _center_crop
from modules.face_match.detector import _detect_face_haar, detect_face
from modules.face_match.embeddings import cosine_similarity, preprocess_arcface
from modules.face_match.models import FaceMatchResult, FaceQuality, MatchDecision
from modules.face_match.quality import apply_super_resolution, assess_quality
from modules.face_match.service import FaceMatchService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_face_image(w: int = 200, h: int = 200) -> np.ndarray:
    """Create a synthetic BGR image with texture."""
    img = np.random.randint(80, 200, (h, w, 3), dtype=np.uint8)
    return img


def _make_image_bytes(image: np.ndarray) -> bytes:
    """Encode image to JPEG bytes."""
    _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buf.tobytes()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestModels:
    def test_match_decision_enum(self):
        assert MatchDecision.MATCH.value == "match"
        assert MatchDecision.NO_MATCH.value == "no_match"
        assert MatchDecision.REVIEW.value == "review"

    def test_face_quality_default(self):
        q = FaceQuality()
        assert q.score == 0.0
        assert q.is_sufficient is False

    def test_face_match_result_default(self):
        r = FaceMatchResult()
        assert r.decision == MatchDecision.NO_MATCH
        assert r.similarity_score == 0.0

    def test_face_match_result_score_bounds(self):
        with pytest.raises(Exception):
            FaceMatchResult(similarity_score=1.5)


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------


class TestEmbeddings:
    def test_preprocess_arcface_shape(self):
        img = _make_face_image(112, 112)
        tensor = preprocess_arcface(img)
        assert tensor.shape == (1, 3, 112, 112)
        assert tensor.dtype == np.float32

    def test_preprocess_arcface_resizes(self):
        img = _make_face_image(200, 200)
        tensor = preprocess_arcface(img)
        assert tensor.shape == (1, 3, 112, 112)

    def test_cosine_similarity_identical(self):
        emb = np.random.rand(512).astype(np.float64)
        emb = emb / np.linalg.norm(emb)
        sim = cosine_similarity(emb, emb)
        assert abs(sim - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        emb_a = np.zeros(512, dtype=np.float64)
        emb_a[0] = 1.0
        emb_b = np.zeros(512, dtype=np.float64)
        emb_b[1] = 1.0
        sim = cosine_similarity(emb_a, emb_b)
        assert abs(sim) < 1e-6

    def test_cosine_similarity_none(self):
        emb = np.random.rand(512)
        assert cosine_similarity(None, emb) == 0.0
        assert cosine_similarity(emb, None) == 0.0

    def test_cosine_similarity_range(self):
        for _ in range(10):
            a = np.random.randn(512)
            a = a / np.linalg.norm(a)
            b = np.random.randn(512)
            b = b / np.linalg.norm(b)
            sim = cosine_similarity(a, b)
            assert -1.0 <= sim <= 1.0


# ---------------------------------------------------------------------------
# Aligner
# ---------------------------------------------------------------------------


class TestAligner:
    def test_align_face_with_landmarks(self):
        img = _make_face_image(300, 300)
        landmarks = [
            [100.0, 120.0],  # left eye
            [200.0, 120.0],  # right eye
            [150.0, 160.0],  # nose
            [110.0, 200.0],  # left mouth
            [190.0, 200.0],  # right mouth
        ]
        aligned = align_face(img, landmarks)
        assert aligned.shape == (112, 112, 3)

    def test_align_face_insufficient_landmarks(self):
        img = _make_face_image(200, 200)
        aligned = align_face(img, [[50.0, 50.0]])
        assert aligned.shape == (112, 112, 3)  # Falls back to center crop

    def test_align_face_from_bbox(self):
        img = _make_face_image(400, 400)
        aligned = align_face_from_bbox(img, [50, 50, 300, 300])
        assert aligned.shape == (112, 112, 3)

    def test_center_crop(self):
        img = _make_face_image(300, 200)
        cropped = _center_crop(img, (112, 112))
        assert cropped.shape == (112, 112, 3)


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class TestDetector:
    def test_detect_face_blank_image(self):
        img = np.full((200, 200, 3), 128, dtype=np.uint8)
        result = detect_face(img)
        # Haar cascade unlikely to detect face in uniform image
        assert isinstance(result.detected, bool)

    def test_detect_face_no_model(self):
        img = _make_face_image(200, 200)
        result = detect_face(img, session=None)
        # Falls back to Haar cascade
        assert result.face_count >= 0

    def test_haar_fallback(self):
        img = np.full((200, 200, 3), 180, dtype=np.uint8)
        result = _detect_face_haar(img)
        assert isinstance(result.detected, bool)


# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------


class TestQuality:
    def test_assess_quality_good_image(self):
        img = _make_face_image(200, 200)
        q = assess_quality(img)
        assert 0.0 <= q.score <= 1.0
        assert q.sharpness > 0
        assert q.brightness > 0
        assert q.size_pixels == 200

    def test_assess_quality_small_image(self):
        img = _make_face_image(30, 30)
        q = assess_quality(img)
        assert q.is_sufficient is False  # Below minimum size

    def test_assess_quality_empty(self):
        q = assess_quality(np.array([]))
        assert q.score == 0.0

    def test_assess_quality_none(self):
        q = assess_quality(None)
        assert q.score == 0.0

    def test_super_resolution_no_model(self):
        img = _make_face_image(50, 50)
        result = apply_super_resolution(img, session=None, scale=4)
        # Falls back to bicubic
        assert result.shape[0] == 200
        assert result.shape[1] == 200

    def test_super_resolution_preserves_channels(self):
        img = _make_face_image(40, 40)
        result = apply_super_resolution(img, session=None, scale=2)
        assert result.shape[2] == 3


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TestFaceMatchService:
    def test_compare_invalid_images(self):
        svc = FaceMatchService()
        result = svc.compare(b"not-an-image", b"not-an-image")
        assert result.decision == MatchDecision.NO_MATCH
        assert result.processing_time_ms >= 0

    def test_compare_valid_images_no_models(self):
        svc = FaceMatchService()
        img = _make_face_image(200, 200)
        img_bytes = _make_image_bytes(img)
        result = svc.compare(img_bytes, img_bytes)
        # Without ONNX models, embeddings will fail → NO_MATCH
        assert isinstance(result, FaceMatchResult)
        assert result.processing_time_ms > 0

    def test_elapsed_ms(self):
        import time
        start = time.perf_counter()
        time.sleep(0.01)
        elapsed = FaceMatchService._elapsed_ms(start)
        assert elapsed >= 10

    def test_decode_valid_image(self):
        img = _make_face_image(100, 100)
        img_bytes = _make_image_bytes(img)
        decoded = FaceMatchService._decode(img_bytes)
        assert decoded is not None
        assert decoded.shape[0] == 100

    def test_decode_invalid_bytes(self):
        decoded = FaceMatchService._decode(b"garbage")
        assert decoded is None

    def test_crop_face(self):
        img = _make_face_image(300, 300)
        cropped = FaceMatchService._crop_face(img, [50, 50, 200, 200])
        assert cropped.shape == (150, 150, 3)

    def test_crop_face_empty_bbox(self):
        img = _make_face_image(200, 200)
        result = FaceMatchService._crop_face(img, [])
        assert result.shape == img.shape
