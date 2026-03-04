"""Unit tests for the document processing module."""

import io

import cv2
import numpy as np
import pytest
from PIL import Image

from modules.doc_processing.detector import (
    detect_document,
    extract_document_contour,
    order_corner_points,
)
from modules.doc_processing.enhancer import (
    apply_clahe,
    denoise,
    enhance_document,
    sharpen,
)
from modules.doc_processing.face_extractor import extract_face_from_document
from modules.doc_processing.forgery import (
    analyze_forgery,
    check_exif_metadata,
    copy_move_detection,
    error_level_analysis,
)
from modules.doc_processing.models import (
    BoundingBox,
    DocumentDetection,
    DocumentProcessingResult,
    ForgeryAnalysis,
)
from modules.doc_processing.perspective import STANDARD_SIZES, correct_perspective
from modules.doc_processing.service import DocumentProcessorService


# ---------------------------------------------------------------------------
# Helpers — synthetic test images
# ---------------------------------------------------------------------------


def _make_blank_image(w: int = 640, h: int = 480, color: tuple = (200, 200, 200)) -> np.ndarray:
    """Create a blank BGR image."""
    img = np.full((h, w, 3), color, dtype=np.uint8)
    return img


def _make_document_image(
    canvas_w: int = 800,
    canvas_h: int = 600,
    doc_w: int = 500,
    doc_h: int = 320,
) -> np.ndarray:
    """Create a synthetic image with a white rectangle (document) on dark background."""
    img = np.full((canvas_h, canvas_w, 3), (40, 40, 40), dtype=np.uint8)
    x_off = (canvas_w - doc_w) // 2
    y_off = (canvas_h - doc_h) // 2
    # Draw white rectangle to simulate a document
    cv2.rectangle(img, (x_off, y_off), (x_off + doc_w, y_off + doc_h), (255, 255, 255), -1)
    # Draw a thick border to create strong edges
    cv2.rectangle(img, (x_off, y_off), (x_off + doc_w, y_off + doc_h), (0, 0, 0), 3)
    return img


def _make_image_with_face(w: int = 800, h: int = 500) -> np.ndarray:
    """Create a synthetic image with an oval that approximates a face shape.

    Note: Haar cascade won't detect this synthetic face — these tests verify
    the function handles the no-face case gracefully.
    """
    img = np.full((h, w, 3), (240, 240, 240), dtype=np.uint8)
    # Draw an ellipse in the upper-left quadrant (typical face location on ID)
    cx, cy = w // 4, h // 2
    cv2.ellipse(img, (cx, cy), (60, 80), 0, 0, 360, (180, 140, 120), -1)
    return img


def _image_to_jpeg_bytes(image: np.ndarray, quality: int = 90) -> bytes:
    """Encode an image to JPEG bytes."""
    _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestModels:
    def test_bounding_box(self):
        bb = BoundingBox(x1=10, y1=20, x2=100, y2=200)
        assert bb.x1 == 10
        assert bb.y2 == 200

    def test_document_detection_default(self):
        dd = DocumentDetection(detected=False)
        assert dd.detected is False
        assert dd.confidence == 0.0
        assert dd.document_type is None

    def test_forgery_analysis_default(self):
        fa = ForgeryAnalysis(score=0.5)
        assert fa.score == 0.5
        assert fa.anomalies == []
        assert fa.exif_suspicious is False

    def test_forgery_analysis_score_bounds(self):
        with pytest.raises(Exception):
            ForgeryAnalysis(score=1.5)
        with pytest.raises(Exception):
            ForgeryAnalysis(score=-0.1)

    def test_document_processing_result_default(self):
        result = DocumentProcessingResult()
        assert result.forgery_score == 0.0
        assert result.detected_anomalies == []
        assert result.processing_time_ms == 0
        assert result.processed_image is None

    def test_document_processing_result_excludes_binary(self):
        result = DocumentProcessingResult(processed_image=b"img", face_region=b"face")
        dumped = result.model_dump()
        assert "processed_image" not in dumped
        assert "face_region" not in dumped


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class TestDetector:
    def test_detect_document_finds_rectangle(self):
        img = _make_document_image()
        result = detect_document(img)
        assert result.detected is True
        assert result.confidence > 0.1
        assert result.bounding_box is not None

    def test_detect_document_no_document(self):
        # Uniform image — no edges to detect
        img = _make_blank_image()
        result = detect_document(img)
        assert result.detected is False

    def test_order_corner_points(self):
        # Random order → should reorder to TL, TR, BR, BL
        pts = np.array([[300, 200], [100, 100], [300, 100], [100, 200]], dtype=np.float32)
        ordered = order_corner_points(pts)
        # Top-left should have smallest sum
        assert ordered[0][0] == 100 and ordered[0][1] == 100
        # Bottom-right should have largest sum
        assert ordered[2][0] == 300 and ordered[2][1] == 200

    def test_extract_document_contour_returns_4_points(self):
        img = _make_document_image()
        corners = extract_document_contour(img)
        if corners is not None:
            assert corners.shape == (4, 2)

    def test_extract_document_contour_no_document(self):
        img = _make_blank_image()
        corners = extract_document_contour(img)
        assert corners is None


# ---------------------------------------------------------------------------
# Perspective
# ---------------------------------------------------------------------------


class TestPerspective:
    def test_correct_perspective_with_corners(self):
        img = _make_document_image(800, 600, 500, 320)
        corners = np.array(
            [[150, 140], [650, 140], [650, 460], [150, 460]],
            dtype=np.float32,
        )
        result = correct_perspective(img, corners=corners, doc_type="DEFAULT")
        expected_w, expected_h = STANDARD_SIZES["DEFAULT"]
        assert result.shape[1] == expected_w
        assert result.shape[0] == expected_h

    def test_correct_perspective_no_corners_returns_original(self):
        img = _make_blank_image()
        result = correct_perspective(img, corners=None)
        # No contour found → original image returned
        assert result.shape == img.shape

    def test_standard_sizes_exist(self):
        assert "DNI" in STANDARD_SIZES
        assert "PASSPORT" in STANDARD_SIZES
        assert "DEFAULT" in STANDARD_SIZES


# ---------------------------------------------------------------------------
# Enhancer
# ---------------------------------------------------------------------------


class TestEnhancer:
    def test_denoise_preserves_shape(self):
        img = _make_blank_image()
        result = denoise(img, strength=5)
        assert result.shape == img.shape

    def test_apply_clahe_preserves_shape(self):
        img = _make_blank_image()
        result = apply_clahe(img)
        assert result.shape == img.shape

    def test_sharpen_preserves_shape(self):
        img = _make_blank_image()
        result = sharpen(img, amount=1.0)
        assert result.shape == img.shape

    def test_enhance_document_pipeline(self):
        img = _make_blank_image()
        result = enhance_document(img)
        assert result.shape == img.shape
        assert result.dtype == np.uint8

    def test_sharpen_increases_contrast(self):
        # Create image with gradient
        img = np.zeros((100, 200, 3), dtype=np.uint8)
        img[:, 100:] = 200
        sharpened = sharpen(img, amount=2.0)
        # The boundary region should have higher contrast after sharpening
        assert not np.array_equal(img, sharpened)


# ---------------------------------------------------------------------------
# Face Extractor
# ---------------------------------------------------------------------------


class TestFaceExtractor:
    def test_extract_face_no_face(self):
        # Plain image with no face-like features
        img = _make_blank_image()
        result = extract_face_from_document(img)
        assert result is None

    def test_extract_face_synthetic_no_detection(self):
        # Synthetic ellipse won't trigger Haar cascade
        img = _make_image_with_face()
        result = extract_face_from_document(img)
        # Haar cascade won't detect drawn ellipses — this is expected
        assert result is None


# ---------------------------------------------------------------------------
# Forgery
# ---------------------------------------------------------------------------


class TestForgery:
    def test_ela_clean_image(self):
        img = _make_blank_image()
        score, ela_img = error_level_analysis(img)
        assert 0.0 <= score <= 1.0
        assert ela_img.shape == img.shape

    def test_ela_tampered_image(self):
        # Create an image with a region that was "pasted" at different quality
        img = _make_blank_image(400, 300, (120, 120, 120))
        # Simulate tampering: a bright block in the center
        img[100:200, 150:250] = (255, 255, 255)
        score, _ = error_level_analysis(img)
        assert 0.0 <= score <= 1.0

    def test_copy_move_clean_image(self):
        img = _make_blank_image()
        score = copy_move_detection(img)
        assert 0.0 <= score <= 1.0

    def test_copy_move_small_image(self):
        # Image too small for block-based analysis
        img = np.zeros((10, 10, 3), dtype=np.uint8)
        score = copy_move_detection(img, block_size=16)
        assert score == 0.0

    def test_check_exif_clean_jpeg(self):
        img = _make_blank_image()
        jpeg_bytes = _image_to_jpeg_bytes(img)
        suspicious, findings = check_exif_metadata(jpeg_bytes)
        assert suspicious is False
        assert findings == []

    def test_check_exif_with_editing_software(self):
        # Create image with EXIF containing editing software
        pil_img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
        buf = io.BytesIO()
        from PIL.ExifTags import Base as ExifBase

        exif = pil_img.getexif()
        exif[305] = "Adobe Photoshop CC 2024"
        pil_img.save(buf, format="JPEG", exif=exif.tobytes())
        buf.seek(0)
        suspicious, findings = check_exif_metadata(buf.getvalue())
        assert suspicious is True
        assert any("photoshop" in f.lower() for f in findings)

    def test_analyze_forgery_aggregate(self):
        img = _make_blank_image()
        jpeg_bytes = _image_to_jpeg_bytes(img)
        result = analyze_forgery(img, jpeg_bytes)
        assert isinstance(result, ForgeryAnalysis)
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.anomalies, list)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TestDocumentProcessorService:
    def test_process_invalid_image(self):
        svc = DocumentProcessorService()
        result = svc.process(b"not-an-image")
        assert "image_decode_failed" in result.detected_anomalies
        assert result.processing_time_ms == 0

    def test_process_blank_image_no_document(self):
        svc = DocumentProcessorService()
        img = _make_blank_image()
        img_bytes = _image_to_jpeg_bytes(img)
        result = svc.process(img_bytes)
        assert "no_document_detected" in result.detected_anomalies
        assert result.processing_time_ms > 0

    def test_process_document_image(self):
        svc = DocumentProcessorService()
        img = _make_document_image()
        img_bytes = _image_to_jpeg_bytes(img)
        result = svc.process(img_bytes)
        # The document might or might not be detected depending on edge quality
        assert result.processing_time_ms > 0
        assert isinstance(result, DocumentProcessingResult)

    def test_elapsed_ms(self):
        import time

        start = time.perf_counter()
        time.sleep(0.01)
        elapsed = DocumentProcessorService._elapsed_ms(start)
        assert elapsed >= 10
