"""OCR engine with fallback chain: PaddleOCR → EasyOCR → Tesseract."""

import cv2
import numpy as np
import structlog

from modules.ocr.models import TextRegion

logger = structlog.get_logger()


class OCREngine:
    """Multi-engine OCR with automatic fallback.

    Primary: PaddleOCR (best accuracy for documents)
    Fallback 1: EasyOCR (good multilingual support)
    Fallback 2: Tesseract (widely available)
    """

    def __init__(self) -> None:
        self._paddle = None
        self._easyocr = None
        self._tesseract_available = False
        self._init_engines()

    def _init_engines(self) -> None:
        """Initialize available OCR engines."""
        # Try PaddleOCR
        try:
            from paddleocr import PaddleOCR

            self._paddle = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                show_log=False,
                use_gpu=False,
            )
            logger.info("ocr_engine.paddleocr_loaded")
        except ImportError:
            logger.warning("ocr_engine.paddleocr_not_available")

        # Try EasyOCR
        try:
            import easyocr

            self._easyocr = easyocr.Reader(["en", "es"], gpu=False, verbose=False)
            logger.info("ocr_engine.easyocr_loaded")
        except ImportError:
            logger.warning("ocr_engine.easyocr_not_available")

        # Try Tesseract
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
            self._tesseract_available = True
            logger.info("ocr_engine.tesseract_loaded")
        except Exception:
            logger.warning("ocr_engine.tesseract_not_available")

    def recognize(self, image: np.ndarray) -> list[TextRegion]:
        """Run OCR on the image using the best available engine.

        Falls back through the chain if the primary engine fails or
        returns low-confidence results.
        """
        # Try PaddleOCR first
        if self._paddle is not None:
            try:
                regions = self._run_paddleocr(image)
                if regions and _avg_confidence(regions) > 0.5:
                    return regions
                logger.debug("ocr_engine.paddleocr_low_confidence, falling back")
            except Exception:
                logger.exception("ocr_engine.paddleocr_error")

        # Fallback to EasyOCR
        if self._easyocr is not None:
            try:
                regions = self._run_easyocr(image)
                if regions and _avg_confidence(regions) > 0.4:
                    return regions
                logger.debug("ocr_engine.easyocr_low_confidence, falling back")
            except Exception:
                logger.exception("ocr_engine.easyocr_error")

        # Fallback to Tesseract
        if self._tesseract_available:
            try:
                return self._run_tesseract(image)
            except Exception:
                logger.exception("ocr_engine.tesseract_error")

        logger.error("ocr_engine.all_engines_failed")
        return []

    @property
    def engine_name(self) -> str:
        """Return the name of the primary available engine."""
        if self._paddle is not None:
            return "paddleocr"
        if self._easyocr is not None:
            return "easyocr"
        if self._tesseract_available:
            return "tesseract"
        return "none"

    def _run_paddleocr(self, image: np.ndarray) -> list[TextRegion]:
        """Run PaddleOCR and return TextRegions."""
        result = self._paddle.ocr(image, cls=True)
        regions: list[TextRegion] = []
        if not result or not result[0]:
            return regions

        for line in result[0]:
            box, (text, conf) = line
            # box is [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            regions.append(TextRegion(
                text=text.strip(),
                confidence=round(float(conf), 4),
                bbox=[int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))],
            ))
        return regions

    def _run_easyocr(self, image: np.ndarray) -> list[TextRegion]:
        """Run EasyOCR and return TextRegions."""
        results = self._easyocr.readtext(image)
        regions: list[TextRegion] = []
        for box, text, conf in results:
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            regions.append(TextRegion(
                text=text.strip(),
                confidence=round(float(conf), 4),
                bbox=[int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))],
            ))
        return regions

    def _run_tesseract(self, image: np.ndarray) -> list[TextRegion]:
        """Run Tesseract and return TextRegions."""
        import pytesseract

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

        regions: list[TextRegion] = []
        n = len(data["text"])
        for i in range(n):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])
            if not text or conf < 0:
                continue
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            regions.append(TextRegion(
                text=text,
                confidence=round(conf / 100.0, 4),
                bbox=[x, y, x + w, y + h],
            ))
        return regions


def _avg_confidence(regions: list[TextRegion]) -> float:
    """Compute average confidence across text regions."""
    if not regions:
        return 0.0
    return sum(r.confidence for r in regions) / len(regions)
