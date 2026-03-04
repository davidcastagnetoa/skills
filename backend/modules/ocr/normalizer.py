"""Data normalizer — cleans and standardizes extracted document fields."""

import re
import unicodedata

import structlog

from modules.ocr.models import ExtractedFields, MRZData, TextRegion

logger = structlog.get_logger()


def _normalize_date_yymmdd(date_str: str) -> str | None:
    """Convert YYMMDD to ISO 8601 (YYYY-MM-DD).

    Uses a pivot year of 30: YY <= 30 → 20YY, YY > 30 → 19YY.
    """
    if not date_str or len(date_str) != 6 or not date_str.isdigit():
        return None

    yy = int(date_str[0:2])
    mm = date_str[2:4]
    dd = date_str[4:6]

    year = 2000 + yy if yy <= 30 else 1900 + yy
    return f"{year}-{mm}-{dd}"


def _normalize_name(name: str) -> str:
    """Normalize a name: remove special chars, title case."""
    if not name:
        return ""
    # Remove non-letter characters except spaces and hyphens
    name = re.sub(r"[^A-Za-zÀ-ÿ\s\-]", "", name)
    # Collapse whitespace
    name = re.sub(r"\s+", " ", name).strip()
    # Title case
    return name.title()


def _normalize_document_number(doc_num: str) -> str:
    """Normalize document number: remove spaces, hyphens, uppercase."""
    if not doc_num:
        return ""
    return re.sub(r"[\s\-]", "", doc_num).upper()


def _strip_accents(text: str) -> str:
    """Strip accent marks for comparison (e.g., García → Garcia)."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize(
    text_regions: list[TextRegion],
    mrz: MRZData | None = None,
) -> ExtractedFields:
    """Normalize and merge OCR text regions with MRZ data.

    Priority: MRZ data takes precedence over visual (VIZ) OCR when available,
    as MRZ is more reliably parsed.
    """
    fields = ExtractedFields()

    # If MRZ is available, use it as the primary source
    if mrz is not None:
        fields.surname = _normalize_name(mrz.surname or "")
        fields.given_names = _normalize_name(mrz.given_names or "")
        fields.full_name = f"{fields.given_names} {fields.surname}".strip() or None
        fields.document_number = _normalize_document_number(mrz.document_number or "")
        fields.date_of_birth = _normalize_date_yymmdd(mrz.date_of_birth or "")
        fields.expiry_date = _normalize_date_yymmdd(mrz.expiry_date or "")
        fields.nationality = mrz.nationality
        fields.sex = mrz.sex
        fields.country_code = mrz.country_code
        fields.document_type = mrz.document_type
        fields.personal_number = mrz.personal_number

    # Augment with VIZ (visual inspection zone) data from OCR regions
    # This could be extended to detect specific field patterns in the text
    if text_regions and not fields.full_name:
        # Heuristic: the longest text region with mostly letters is likely the name
        name_candidates = [
            r for r in text_regions
            if len(r.text) > 5
            and sum(c.isalpha() or c == " " for c in r.text) / len(r.text) > 0.7
            and r.confidence > 0.5
        ]
        if name_candidates:
            best = max(name_candidates, key=lambda r: r.confidence)
            fields.full_name = _normalize_name(best.text)

    logger.debug(
        "normalizer.complete",
        has_mrz=mrz is not None,
        full_name=fields.full_name,
        doc_number=fields.document_number,
    )

    return fields
