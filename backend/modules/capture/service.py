"""Capture validation service — orchestrates all capture checks."""

import cv2
import numpy as np
import structlog

from modules.capture.gallery_blocker import check_gallery_upload
from modules.capture.models import CaptureValidationResult, QualityIssue
from modules.capture.quality import validate_image_quality, validate_payload_size
from modules.capture.virtual_camera import (
    detect_virtual_camera_from_metadata,
    detect_virtual_camera_from_stream_info,
)

logger = structlog.get_logger()


class CaptureValidationService:
    """Validates captured images before processing.

    Checks:
    1. Payload size (max 10 MB)
    2. Image quality (sharpness, brightness, resolution, face presence)
    3. Virtual camera detection
    4. Gallery upload detection
    """

    def validate(
        self,
        image_bytes: bytes,
        device_name: str | None = None,
        framerate: float | None = None,
    ) -> CaptureValidationResult:
        """Validate a captured image.

        Args:
            image_bytes: Raw image bytes (JPEG/PNG).
            device_name: Camera device name from client.
            framerate: Reported stream framerate.
        """
        all_issues: list[QualityIssue] = []

        # 1. Payload size
        size_issue = validate_payload_size(image_bytes)
        if size_issue:
            all_issues.append(size_issue)
            return CaptureValidationResult(is_valid=False, issues=all_issues)

        # 2. Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            all_issues.append(QualityIssue(
                code="decode_failed",
                message="Failed to decode image",
            ))
            return CaptureValidationResult(is_valid=False, issues=all_issues)

        # 3. Image quality
        quality = validate_image_quality(image)
        all_issues.extend(quality.issues)

        # 4. Virtual camera detection
        vc_meta = detect_virtual_camera_from_metadata(image_bytes)
        vc_stream = detect_virtual_camera_from_stream_info(device_name, framerate)

        # Merge: use the more confident detection
        virtual_camera = vc_meta if vc_meta.confidence > vc_stream.confidence else vc_stream
        if virtual_camera.is_virtual:
            all_issues.append(QualityIssue(
                code="virtual_camera_detected",
                message=f"Virtual camera detected: {virtual_camera.detected_driver}",
            ))

        # 5. Gallery upload check
        gallery = check_gallery_upload(image_bytes)
        if gallery.is_from_gallery:
            all_issues.append(QualityIssue(
                code="gallery_upload_detected",
                message="Image appears to be from gallery, not live capture",
            ))

        # Final decision
        blocking_issues = [i for i in all_issues if i.severity == "error"]
        is_valid = len(blocking_issues) == 0

        logger.info(
            "capture_validation.complete",
            is_valid=is_valid,
            quality_score=quality.quality_score,
            n_issues=len(all_issues),
            virtual_camera=virtual_camera.is_virtual,
            gallery=gallery.is_from_gallery,
        )

        return CaptureValidationResult(
            is_valid=is_valid,
            quality=quality,
            virtual_camera=virtual_camera,
            gallery_check=gallery,
            issues=all_issues,
        )
