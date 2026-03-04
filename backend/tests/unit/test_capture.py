"""Unit tests for the capture validation module."""

import io

import cv2
import numpy as np
import pytest
from PIL import Image

from modules.capture.gallery_blocker import check_gallery_upload
from modules.capture.models import CaptureValidationResult, QualityIssue
from modules.capture.quality import validate_image_quality, validate_payload_size
from modules.capture.service import CaptureValidationService
from modules.capture.virtual_camera import (
    detect_virtual_camera_from_metadata,
    detect_virtual_camera_from_stream_info,
)


def _make_image(w: int = 800, h: int = 600) -> np.ndarray:
    img = np.random.randint(80, 200, (h, w, 3), dtype=np.uint8)
    return img


def _to_jpeg(image: np.ndarray, quality: int = 90) -> bytes:
    _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes()


def _make_jpeg_with_exif(software: str = "") -> bytes:
    pil_img = Image.fromarray(np.random.randint(80, 200, (600, 800, 3), dtype=np.uint8))
    buf = io.BytesIO()
    exif = pil_img.getexif()
    if software:
        exif[305] = software
    pil_img.save(buf, format="JPEG", exif=exif.tobytes())
    return buf.getvalue()


class TestImageQuality:
    def test_good_image(self):
        img = _make_image(800, 600)
        result = validate_image_quality(img)
        assert result.sharpness > 0
        assert result.brightness > 0
        assert result.resolution_ok is True

    def test_low_resolution(self):
        img = _make_image(320, 240)
        result = validate_image_quality(img)
        assert result.resolution_ok is False
        assert any(i.code == "low_resolution" for i in result.issues)

    def test_dark_image(self):
        img = np.full((600, 800, 3), 10, dtype=np.uint8)
        result = validate_image_quality(img)
        assert any(i.code == "too_dark" for i in result.issues)

    def test_overexposed_image(self):
        img = np.full((600, 800, 3), 250, dtype=np.uint8)
        result = validate_image_quality(img)
        assert any(i.code == "too_bright" for i in result.issues)

    def test_blurry_image(self):
        img = np.full((600, 800, 3), 128, dtype=np.uint8)  # Uniform = zero sharpness
        result = validate_image_quality(img)
        assert any(i.code == "too_blurry" for i in result.issues)


class TestPayloadSize:
    def test_normal_size(self):
        data = b"x" * (5 * 1024 * 1024)  # 5 MB
        assert validate_payload_size(data) is None

    def test_too_large(self):
        data = b"x" * (11 * 1024 * 1024)  # 11 MB
        issue = validate_payload_size(data)
        assert issue is not None
        assert issue.code == "payload_too_large"


class TestVirtualCamera:
    def test_no_virtual_camera(self):
        jpeg = _to_jpeg(_make_image())
        result = detect_virtual_camera_from_metadata(jpeg)
        assert result.is_virtual is False

    def test_obs_in_exif(self):
        jpeg = _make_jpeg_with_exif("OBS Virtual Camera")
        result = detect_virtual_camera_from_metadata(jpeg)
        assert result.is_virtual is True
        assert result.confidence > 0.9

    def test_manycam_in_exif(self):
        jpeg = _make_jpeg_with_exif("ManyCam 7.0")
        result = detect_virtual_camera_from_metadata(jpeg)
        assert result.is_virtual is True

    def test_stream_info_obs(self):
        result = detect_virtual_camera_from_stream_info(device_name="OBS Virtual Camera")
        assert result.is_virtual is True

    def test_stream_info_normal(self):
        result = detect_virtual_camera_from_stream_info(device_name="HD Webcam C920")
        assert result.is_virtual is False


class TestGalleryBlocker:
    def test_normal_jpeg(self):
        jpeg = _to_jpeg(_make_image())
        result = check_gallery_upload(jpeg)
        assert result.is_from_gallery is False

    def test_gallery_software(self):
        jpeg = _make_jpeg_with_exif("Google Photos 5.0")
        result = check_gallery_upload(jpeg)
        assert result.is_from_gallery is True
        assert any("gallery_software" in r for r in result.reasons)


class TestCaptureValidationService:
    def test_valid_image(self):
        svc = CaptureValidationService()
        img = _make_image(800, 600)
        result = svc.validate(_to_jpeg(img))
        assert isinstance(result, CaptureValidationResult)

    def test_invalid_bytes(self):
        svc = CaptureValidationService()
        result = svc.validate(b"not-an-image")
        assert result.is_valid is False
        assert any(i.code == "decode_failed" for i in result.issues)

    def test_oversized_payload(self):
        svc = CaptureValidationService()
        result = svc.validate(b"x" * (11 * 1024 * 1024))
        assert result.is_valid is False
        assert any(i.code == "payload_too_large" for i in result.issues)

    def test_virtual_camera_blocked(self):
        svc = CaptureValidationService()
        img = _make_image(800, 600)
        result = svc.validate(_to_jpeg(img), device_name="OBS Virtual Camera")
        assert any(i.code == "virtual_camera_detected" for i in result.issues)
