"""Virtual camera detection.

Detects known virtual camera drivers and suspicious stream characteristics
that may indicate video injection attacks.
"""

import io
import re

import structlog
from PIL import Image

from modules.capture.models import VirtualCameraResult

logger = structlog.get_logger()

# Known virtual camera driver signatures
_VIRTUAL_CAMERA_SIGNATURES = [
    "obs virtual camera",
    "obs-camera",
    "manycam",
    "snap camera",
    "snapcam",
    "xsplit vcam",
    "chromacam",
    "e2esoft vcam",
    "droidcam",
    "iriun",
    "epoccam",
    "camo",
    "mmhmm",
    "virtual camera",
    "virtualcam",
]


def detect_virtual_camera_from_metadata(image_bytes: bytes) -> VirtualCameraResult:
    """Check image metadata for virtual camera indicators.

    Analyzes EXIF data for:
    - Known virtual camera software tags
    - Suspicious device model strings
    - Missing or inconsistent camera metadata
    """
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        exif = pil_img.getexif()

        if not exif:
            # No EXIF is suspicious for camera captures (but not definitive)
            return VirtualCameraResult(is_virtual=False, confidence=0.2)

        # Check software tag (305)
        software = str(exif.get(305, "")).lower()
        for sig in _VIRTUAL_CAMERA_SIGNATURES:
            if sig in software:
                logger.warning("virtual_camera.detected_in_exif", software=software)
                return VirtualCameraResult(
                    is_virtual=True,
                    detected_driver=software,
                    confidence=0.95,
                )

        # Check device model tag (272)
        model = str(exif.get(272, "")).lower()
        for sig in _VIRTUAL_CAMERA_SIGNATURES:
            if sig in model:
                return VirtualCameraResult(
                    is_virtual=True,
                    detected_driver=model,
                    confidence=0.9,
                )

    except Exception:
        pass

    return VirtualCameraResult(is_virtual=False, confidence=0.1)


def detect_virtual_camera_from_stream_info(
    device_name: str | None = None,
    framerate: float | None = None,
    resolution: tuple[int, int] | None = None,
) -> VirtualCameraResult:
    """Check stream metadata provided by the client for virtual camera indicators.

    Args:
        device_name: Camera device name from the client.
        framerate: Reported framerate.
        resolution: Reported resolution (width, height).
    """
    if device_name:
        name_lower = device_name.lower()
        for sig in _VIRTUAL_CAMERA_SIGNATURES:
            if sig in name_lower:
                return VirtualCameraResult(
                    is_virtual=True,
                    detected_driver=device_name,
                    confidence=0.95,
                )

    # Suspicious framerate (virtual cameras often have non-standard rates)
    if framerate is not None and framerate not in (15, 24, 25, 29.97, 30, 50, 59.94, 60):
        return VirtualCameraResult(
            is_virtual=False,
            confidence=0.3,  # Mildly suspicious
        )

    return VirtualCameraResult(is_virtual=False, confidence=0.05)
