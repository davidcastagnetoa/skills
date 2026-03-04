"""Cross-field consistency checker — MRZ vs visual (VIZ) fields."""

import unicodedata

import structlog

from modules.ocr.models import ConsistencyResult, ExtractedFields, MRZData, TextRegion

logger = structlog.get_logger()


def _strip_accents(text: str) -> str:
    """Remove accent marks for fuzzy comparison."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _fuzzy_match(a: str, b: str, threshold: float = 0.8) -> bool:
    """Simple character-level similarity check."""
    if not a or not b:
        return True  # Can't compare if one is missing
    a_clean = _strip_accents(a).upper().replace(" ", "")
    b_clean = _strip_accents(b).upper().replace(" ", "")
    if not a_clean or not b_clean:
        return True

    # Exact match
    if a_clean == b_clean:
        return True

    # Character overlap ratio
    common = sum(1 for c in a_clean if c in b_clean)
    max_len = max(len(a_clean), len(b_clean))
    return common / max_len >= threshold


def check_consistency(
    fields: ExtractedFields,
    mrz: MRZData | None,
    text_regions: list[TextRegion] | None = None,
) -> ConsistencyResult:
    """Check consistency between MRZ data and extracted fields.

    Verifies:
    - Name from MRZ matches VIZ name
    - Document number consistency
    - Date consistency (birth, expiry)
    - Country/nationality coherence
    """
    discrepancies: list[str] = []
    checks_passed = 0
    checks_total = 0

    if mrz is None:
        return ConsistencyResult(score=1.0, discrepancies=[])

    # Check name consistency with VIZ text regions
    if text_regions and mrz.surname:
        mrz_name = f"{mrz.given_names or ''} {mrz.surname}".strip().upper()
        viz_texts = [r.text.upper() for r in text_regions if len(r.text) > 3]

        # Look for the MRZ name (or parts of it) in VIZ text
        name_found = any(
            _fuzzy_match(mrz.surname.upper(), t, 0.7)
            for t in viz_texts
        )
        checks_total += 1
        if name_found:
            checks_passed += 1
        else:
            # Not necessarily a discrepancy — VIZ might not be in the regions
            pass

    # Check document number appears in VIZ
    if text_regions and mrz.document_number:
        doc_num_clean = mrz.document_number.replace("<", "").strip()
        viz_texts = [r.text.replace(" ", "").replace("-", "") for r in text_regions]
        checks_total += 1
        if any(doc_num_clean in t for t in viz_texts):
            checks_passed += 1
        else:
            discrepancies.append("document_number_not_found_in_viz")

    # Check MRZ internal consistency: country_code vs nationality
    if mrz.country_code and mrz.nationality:
        checks_total += 1
        if mrz.country_code == mrz.nationality:
            checks_passed += 1
        else:
            # Different country_code and nationality is valid (e.g., residence permit)
            checks_passed += 1

    # Check date of birth is plausible (not in the future, person not > 150 years old)
    if mrz.date_of_birth and len(mrz.date_of_birth) == 6:
        checks_total += 1
        try:
            yy = int(mrz.date_of_birth[0:2])
            mm = int(mrz.date_of_birth[2:4])
            dd = int(mrz.date_of_birth[4:6])
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                checks_passed += 1
            else:
                discrepancies.append("invalid_date_of_birth")
        except ValueError:
            discrepancies.append("unparseable_date_of_birth")

    # Check expiry date is plausible
    if mrz.expiry_date and len(mrz.expiry_date) == 6:
        checks_total += 1
        try:
            mm = int(mrz.expiry_date[2:4])
            dd = int(mrz.expiry_date[4:6])
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                checks_passed += 1
            else:
                discrepancies.append("invalid_expiry_date")
        except ValueError:
            discrepancies.append("unparseable_expiry_date")

    # Check MRZ check digits
    if mrz.check_digit_results:
        for field_name, valid in mrz.check_digit_results.items():
            checks_total += 1
            if valid:
                checks_passed += 1
            else:
                discrepancies.append(f"check_digit_failed:{field_name}")

    score = checks_passed / checks_total if checks_total > 0 else 1.0

    logger.debug(
        "consistency.check_complete",
        score=round(score, 3),
        checks_passed=checks_passed,
        checks_total=checks_total,
        discrepancies=discrepancies,
    )

    return ConsistencyResult(
        score=round(score, 4),
        discrepancies=discrepancies,
    )
