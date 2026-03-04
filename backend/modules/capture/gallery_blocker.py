"""Gallery upload blocker.

Detects images that were uploaded from a device gallery rather than
captured live from the camera.
"""

import io
from datetime import datetime, timezone

import structlog
from PIL import Image

from modules.capture.models import GalleryCheckResult

logger = structlog.get_logger()

# Maximum age in seconds for a "live" capture
_MAX_CAPTURE_AGE_SECONDS = 60


def check_gallery_upload(image_bytes: bytes) -> GalleryCheckResult:
    """Analyze image to determine if it was uploaded from gallery.

    Indicators of gallery upload:
    - EXIF timestamp too old (> 60 seconds)
    - Presence of editing software in EXIF
    - Image dimensions suggesting a screenshot (exact screen resolutions)
    """
    reasons: list[str] = []

    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        exif = pil_img.getexif()

        if exif:
            # Check capture timestamp
            date_original = exif.get(36867)  # DateTimeOriginal
            if date_original:
                try:
                    captured = datetime.strptime(str(date_original), "%Y:%m:%d %H:%M:%S")
                    captured = captured.replace(tzinfo=timezone.utc)
                    age = (datetime.now(timezone.utc) - captured).total_seconds()
                    if age > _MAX_CAPTURE_AGE_SECONDS:
                        reasons.append(f"capture_timestamp_too_old:{int(age)}s")
                except ValueError:
                    pass

            # Check for editing software
            software = str(exif.get(305, "")).lower()
            gallery_indicators = ["photos", "gallery", "album", "screenshot"]
            for indicator in gallery_indicators:
                if indicator in software:
                    reasons.append(f"gallery_software_detected:{software}")

        # Check for common screenshot resolutions
        w, h = pil_img.size
        screenshot_resolutions = [
            (1920, 1080), (2560, 1440), (3840, 2160),  # Desktop
            (1080, 1920), (1440, 2560),  # Mobile portrait
            (1125, 2436), (1170, 2532), (1284, 2778),  # iPhone
            (1080, 2340), (1080, 2400), (1440, 3200),  # Android
        ]
        if (w, h) in screenshot_resolutions or (h, w) in screenshot_resolutions:
            reasons.append(f"screenshot_resolution_detected:{w}x{h}")

    except Exception:
        pass

    is_gallery = len(reasons) > 0

    if is_gallery:
        logger.info("gallery_blocker.detected", reasons=reasons)

    return GalleryCheckResult(
        is_from_gallery=is_gallery,
        reasons=reasons,
    )
