"""MRZ (Machine Readable Zone) parser — ICAO 9303 compliant.

Supports:
- TD1 (3 lines × 30 chars): National ID cards
- TD2 (2 lines × 36 chars): Travel documents
- TD3 (2 lines × 44 chars): Passports
"""

import re

import structlog

from modules.ocr.models import MRZData

logger = structlog.get_logger()

# ICAO 9303 check digit weights
_WEIGHTS = [7, 3, 1]

# Characters allowed in MRZ
_MRZ_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")


def _char_value(c: str) -> int:
    """Convert MRZ character to numeric value for check digit calculation."""
    if c == "<":
        return 0
    if c.isdigit():
        return int(c)
    if c.isalpha():
        return ord(c.upper()) - ord("A") + 10
    return 0


def compute_check_digit(data: str) -> int:
    """Compute ICAO 9303 check digit for a given string."""
    total = 0
    for i, c in enumerate(data):
        total += _char_value(c) * _WEIGHTS[i % 3]
    return total % 10


def validate_check_digit(data: str, check: str) -> bool:
    """Validate that the check digit matches the data."""
    if not check.isdigit():
        return False
    return compute_check_digit(data) == int(check)


def _clean_mrz_text(text: str) -> str:
    """Clean OCR artifacts from MRZ text."""
    # Replace common OCR errors
    text = text.upper()
    text = text.replace("O", "0").replace("I", "1").replace("S", "5")
    # Only keep MRZ-valid characters after replacement
    text = re.sub(r"[^A-Z0-9<]", "<", text)
    return text


def _parse_name(name_field: str) -> tuple[str, str]:
    """Parse name field: SURNAME<<GIVEN<NAMES → (surname, given_names)."""
    parts = name_field.split("<<")
    surname = parts[0].replace("<", " ").strip() if parts else ""
    given_names = parts[1].replace("<", " ").strip() if len(parts) > 1 else ""
    return surname, given_names


def detect_mrz_lines(text_lines: list[str]) -> list[str]:
    """Detect MRZ lines from OCR output.

    MRZ lines are identified by their character composition (mostly
    uppercase letters, digits, and '<' fillers) and length.
    """
    mrz_candidates: list[str] = []

    for line in text_lines:
        cleaned = line.strip().upper()
        if len(cleaned) < 28:
            continue

        # Count MRZ-valid characters
        mrz_chars = sum(1 for c in cleaned if c in _MRZ_CHARS)
        ratio = mrz_chars / len(cleaned)

        if ratio > 0.85 and len(cleaned) >= 28:
            mrz_candidates.append(cleaned)

    return mrz_candidates


def parse_td3(lines: list[str]) -> MRZData:
    """Parse TD3 (passport) MRZ: 2 lines × 44 characters."""
    line1 = lines[0].ljust(44, "<")[:44]
    line2 = lines[1].ljust(44, "<")[:44]

    doc_type = line1[0:2].replace("<", "").strip()
    country = line1[2:5].replace("<", "").strip()
    surname, given_names = _parse_name(line1[5:44])

    doc_number = line2[0:9].replace("<", "").strip()
    doc_check = line2[9]
    nationality = line2[10:13].replace("<", "").strip()
    dob = line2[13:19]
    dob_check = line2[19]
    sex = line2[20].replace("<", "")
    expiry = line2[21:27]
    expiry_check = line2[27]
    personal_number = line2[28:42].replace("<", "").strip()
    personal_check = line2[42]
    composite_check = line2[43]

    check_results = {
        "document_number": validate_check_digit(line2[0:9], doc_check),
        "date_of_birth": validate_check_digit(dob, dob_check),
        "expiry_date": validate_check_digit(expiry, expiry_check),
    }

    if personal_number:
        check_results["personal_number"] = validate_check_digit(line2[28:42], personal_check)

    # Composite check digit (all data fields)
    composite_data = line2[0:10] + line2[13:20] + line2[21:43]
    check_results["composite"] = validate_check_digit(composite_data, composite_check)

    all_valid = all(check_results.values())

    return MRZData(
        raw_lines=[line1, line2],
        document_type=doc_type or "P",
        country_code=country,
        surname=surname,
        given_names=given_names,
        document_number=doc_number,
        nationality=nationality,
        date_of_birth=dob,
        sex=sex if sex in ("M", "F", "X") else None,
        expiry_date=expiry,
        personal_number=personal_number or None,
        is_valid=all_valid,
        check_digit_results=check_results,
    )


def parse_td1(lines: list[str]) -> MRZData:
    """Parse TD1 (national ID) MRZ: 3 lines × 30 characters."""
    line1 = lines[0].ljust(30, "<")[:30]
    line2 = lines[1].ljust(30, "<")[:30]
    line3 = lines[2].ljust(30, "<")[:30]

    doc_type = line1[0:2].replace("<", "").strip()
    country = line1[2:5].replace("<", "").strip()
    doc_number = line1[5:14].replace("<", "").strip()
    doc_check = line1[14]
    optional1 = line1[15:30].replace("<", "").strip()

    dob = line2[0:6]
    dob_check = line2[6]
    sex = line2[7].replace("<", "")
    expiry = line2[8:14]
    expiry_check = line2[14]
    nationality = line2[15:18].replace("<", "").strip()
    optional2 = line2[18:29].replace("<", "").strip()
    composite_check = line2[29]

    surname, given_names = _parse_name(line3[0:30])

    check_results = {
        "document_number": validate_check_digit(line1[5:14], doc_check),
        "date_of_birth": validate_check_digit(dob, dob_check),
        "expiry_date": validate_check_digit(expiry, expiry_check),
    }

    # Composite: line1[5:30] + line2[0:7] + line2[8:15] + line2[18:29]
    composite_data = line1[5:30] + line2[0:7] + line2[8:15] + line2[18:29]
    check_results["composite"] = validate_check_digit(composite_data, composite_check)

    all_valid = all(check_results.values())

    return MRZData(
        raw_lines=[line1, line2, line3],
        document_type=doc_type or "ID",
        country_code=country,
        surname=surname,
        given_names=given_names,
        document_number=doc_number,
        nationality=nationality,
        date_of_birth=dob,
        sex=sex if sex in ("M", "F", "X") else None,
        expiry_date=expiry,
        personal_number=optional1 or optional2 or None,
        is_valid=all_valid,
        check_digit_results=check_results,
    )


def parse_mrz(lines: list[str]) -> MRZData | None:
    """Auto-detect MRZ format and parse.

    Args:
        lines: List of MRZ text lines.

    Returns:
        Parsed MRZData or None if format not recognized.
    """
    if not lines:
        return None

    # Determine format by number of lines and length
    if len(lines) >= 3 and all(len(l) >= 28 for l in lines[:3]):
        # TD1: 3 lines × 30
        logger.debug("mrz_parser.detected_td1")
        return parse_td1(lines[:3])

    if len(lines) >= 2:
        avg_len = sum(len(l) for l in lines[:2]) / 2
        if avg_len >= 40:
            # TD3: 2 lines × 44
            logger.debug("mrz_parser.detected_td3")
            return parse_td3(lines[:2])
        if avg_len >= 33:
            # TD2: 2 lines × 36 — similar to TD3 but shorter
            logger.debug("mrz_parser.detected_td2_as_td3")
            return parse_td3(lines[:2])

    logger.debug("mrz_parser.format_not_recognized", n_lines=len(lines))
    return None
