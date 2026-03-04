"""OCR service — orchestrates text extraction, MRZ parsing, normalization, and validation."""

import time

import cv2
import numpy as np
import structlog

from modules.ocr.consistency import check_consistency
from modules.ocr.engine import OCREngine
from modules.ocr.expiry import validate_expiry
from modules.ocr.models import OCRResult
from modules.ocr.mrz_parser import detect_mrz_lines, parse_mrz
from modules.ocr.normalizer import normalize

logger = structlog.get_logger()


class OCRService:
    """Orchestrates the full OCR pipeline.

    Pipeline:
        1. Run OCR engine on the document image.
        2. Detect and parse MRZ lines.
        3. Normalize extracted fields.
        4. Check consistency between MRZ and VIZ data.
        5. Validate document expiry.
    """

    def __init__(self) -> None:
        self._engine = OCREngine()

    def extract(self, image_bytes: bytes) -> OCRResult:
        """Extract text and structured data from a document image.

        Args:
            image_bytes: Document image bytes (JPEG/PNG), already enhanced.

        Returns:
            OCRResult with extracted fields, MRZ, consistency, and expiry status.
        """
        start = time.perf_counter()

        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return OCRResult(processing_time_ms=0)

        # 1. Run OCR
        text_regions = self._engine.recognize(image)
        avg_conf = (
            sum(r.confidence for r in text_regions) / len(text_regions)
            if text_regions
            else 0.0
        )

        # 2. Detect and parse MRZ
        all_texts = [r.text for r in text_regions]
        mrz_lines = detect_mrz_lines(all_texts)
        mrz_data = parse_mrz(mrz_lines)

        # 3. Normalize fields
        fields = normalize(text_regions, mrz_data)

        # 4. Consistency check
        consistency = check_consistency(fields, mrz_data, text_regions)

        # 5. Expiry validation
        expiry = validate_expiry(fields.expiry_date)

        elapsed = int((time.perf_counter() - start) * 1000)

        logger.info(
            "ocr_service.complete",
            engine=self._engine.engine_name,
            n_regions=len(text_regions),
            mrz_found=mrz_data is not None,
            mrz_valid=mrz_data.is_valid if mrz_data else False,
            consistency_score=consistency.score,
            is_expired=expiry.is_expired,
            elapsed_ms=elapsed,
        )

        return OCRResult(
            fields=fields,
            mrz_data=mrz_data,
            mrz_valid=mrz_data.is_valid if mrz_data else False,
            text_regions=text_regions,
            data_consistency_score=consistency.score,
            consistency_discrepancies=consistency.discrepancies,
            is_expired=expiry.is_expired,
            expiry_warning=expiry.warning,
            ocr_confidence=round(avg_conf, 4),
            engine_used=self._engine.engine_name,
            processing_time_ms=elapsed,
        )
