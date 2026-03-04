"""Unit tests for the OCR module."""

from datetime import date, timedelta

import pytest

from modules.ocr.consistency import check_consistency
from modules.ocr.expiry import validate_expiry
from modules.ocr.models import (
    ConsistencyResult,
    ExtractedFields,
    ExpiryResult,
    MRZData,
    OCRResult,
    TextRegion,
)
from modules.ocr.mrz_parser import (
    compute_check_digit,
    detect_mrz_lines,
    parse_mrz,
    parse_td1,
    parse_td3,
    validate_check_digit,
)
from modules.ocr.normalizer import normalize


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestModels:
    def test_text_region(self):
        r = TextRegion(text="HELLO", confidence=0.95, bbox=[10, 20, 100, 50])
        assert r.text == "HELLO"
        assert r.confidence == 0.95

    def test_mrz_data_default(self):
        m = MRZData()
        assert m.is_valid is False
        assert m.raw_lines == []

    def test_extracted_fields_default(self):
        f = ExtractedFields()
        assert f.full_name is None
        assert f.document_number is None

    def test_ocr_result_default(self):
        r = OCRResult()
        assert r.mrz_valid is False
        assert r.data_consistency_score == 1.0
        assert r.engine_used == "paddleocr"


# ---------------------------------------------------------------------------
# MRZ Parser
# ---------------------------------------------------------------------------


class TestMRZParser:
    def test_check_digit_known_values(self):
        # ICAO 9303 example: "AB1234567" → check digit
        assert isinstance(compute_check_digit("AB1234567"), int)
        assert 0 <= compute_check_digit("AB1234567") <= 9

    def test_check_digit_all_zeros(self):
        assert compute_check_digit("000000") == 0

    def test_check_digit_filler(self):
        assert compute_check_digit("<<<<<<") == 0

    def test_validate_check_digit(self):
        data = "L898902C3"
        cd = str(compute_check_digit(data))
        assert validate_check_digit(data, cd) is True
        assert validate_check_digit(data, "0" if cd != "0" else "1") is (cd == "0" or False)

    def test_validate_check_digit_non_digit(self):
        assert validate_check_digit("ABC", "X") is False

    def test_detect_mrz_lines_passport(self):
        lines = [
            "Some header text on the document",
            "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
            "L898902C36UTO7408122F1204159ZE184226B<<<<<10",
            "More text below",
        ]
        mrz = detect_mrz_lines(lines)
        assert len(mrz) >= 2

    def test_detect_mrz_lines_no_mrz(self):
        lines = ["Hello world", "Short", "Not MRZ"]
        mrz = detect_mrz_lines(lines)
        assert len(mrz) == 0

    def test_parse_td3_passport(self):
        # Standard ICAO example (with valid structure)
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
        result = parse_td3([line1, line2])
        assert result.document_type == "P"
        assert result.country_code == "UTO"
        assert result.surname == "Eriksson"
        assert "Anna Maria" in result.given_names
        assert result.document_number == "L898902C3"
        assert result.nationality == "UTO"
        assert result.date_of_birth == "740812"
        assert result.sex == "F"
        assert result.expiry_date == "120415"

    def test_parse_td1_id_card(self):
        line1 = "IDUTOD231458907<<<<<<<<<<<<<<<<<"
        line2 = "7408122F1204159UTO<<<<<<<<<<<6<<"
        line3 = "ERIKSSON<<ANNA<MARIA<<<<<<<<<<<<"
        result = parse_td1([line1, line2, line3])
        assert result.document_type == "ID"
        assert result.surname == "Eriksson"
        assert "Anna Maria" in result.given_names

    def test_parse_mrz_auto_detects_td3(self):
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
        result = parse_mrz([line1, line2])
        assert result is not None
        assert result.document_type == "P"

    def test_parse_mrz_empty(self):
        result = parse_mrz([])
        assert result is None

    def test_parse_mrz_short_lines(self):
        result = parse_mrz(["SHORT", "LINES"])
        assert result is None


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------


class TestNormalizer:
    def test_normalize_with_mrz(self):
        mrz = MRZData(
            surname="GARCIA",
            given_names="MARIA ELENA",
            document_number="ABC123456",
            date_of_birth="900315",
            expiry_date="251231",
            nationality="ESP",
            sex="F",
            country_code="ESP",
            document_type="ID",
        )
        fields = normalize([], mrz)
        assert fields.surname == "Garcia"
        assert fields.given_names == "Maria Elena"
        assert fields.full_name == "Maria Elena Garcia"
        assert fields.document_number == "ABC123456"
        assert fields.date_of_birth == "1990-03-15"
        assert fields.expiry_date == "2025-12-31"
        assert fields.nationality == "ESP"

    def test_normalize_date_yymmdd_pivot(self):
        # Year <= 30 → 20xx
        mrz = MRZData(date_of_birth="250101", expiry_date="300601")
        fields = normalize([], mrz)
        assert fields.date_of_birth == "2025-01-01"
        assert fields.expiry_date == "2030-06-01"

    def test_normalize_date_yymmdd_old(self):
        # Year > 30 → 19xx
        mrz = MRZData(date_of_birth="850720")
        fields = normalize([], mrz)
        assert fields.date_of_birth == "1985-07-20"

    def test_normalize_without_mrz_uses_text_regions(self):
        regions = [
            TextRegion(text="GARCIA MARTINEZ MARIA", confidence=0.9, bbox=[0, 0, 100, 20]),
            TextRegion(text="12345", confidence=0.95, bbox=[0, 20, 50, 30]),
        ]
        fields = normalize(regions, None)
        assert fields.full_name is not None
        assert "Garcia" in fields.full_name

    def test_normalize_document_number_cleaned(self):
        mrz = MRZData(document_number="ABC 123-456")
        fields = normalize([], mrz)
        assert fields.document_number == "ABC123456"


# ---------------------------------------------------------------------------
# Consistency Checker
# ---------------------------------------------------------------------------


class TestConsistency:
    def test_consistency_no_mrz(self):
        fields = ExtractedFields()
        result = check_consistency(fields, None)
        assert result.score == 1.0
        assert result.discrepancies == []

    def test_consistency_valid_mrz(self):
        mrz = MRZData(
            surname="GARCIA",
            given_names="MARIA",
            document_number="ABC123",
            date_of_birth="900315",
            expiry_date="251231",
            country_code="ESP",
            nationality="ESP",
            check_digit_results={"document_number": True, "date_of_birth": True},
        )
        fields = ExtractedFields(full_name="Maria Garcia", document_number="ABC123")
        result = check_consistency(fields, mrz)
        assert result.score > 0.5
        assert isinstance(result.discrepancies, list)

    def test_consistency_failed_check_digits(self):
        mrz = MRZData(
            date_of_birth="900315",
            expiry_date="251231",
            check_digit_results={
                "document_number": False,
                "date_of_birth": False,
            },
        )
        fields = ExtractedFields()
        result = check_consistency(fields, mrz)
        assert result.score < 1.0
        assert any("check_digit_failed" in d for d in result.discrepancies)

    def test_consistency_invalid_date(self):
        mrz = MRZData(date_of_birth="991399")  # month 13
        fields = ExtractedFields()
        result = check_consistency(fields, mrz)
        assert any("invalid_date" in d for d in result.discrepancies)


# ---------------------------------------------------------------------------
# Expiry Validator
# ---------------------------------------------------------------------------


class TestExpiry:
    def test_expired_document(self):
        past = (date.today() - timedelta(days=30)).isoformat()
        result = validate_expiry(past)
        assert result.is_expired is True
        assert result.days_until_expiry is not None
        assert result.days_until_expiry < 0

    def test_expiring_soon(self):
        soon = (date.today() + timedelta(days=15)).isoformat()
        result = validate_expiry(soon)
        assert result.is_expired is False
        assert result.warning == "expires_within_30_days"

    def test_valid_document(self):
        future = (date.today() + timedelta(days=365)).isoformat()
        result = validate_expiry(future)
        assert result.is_expired is False
        assert result.warning is None
        assert result.days_until_expiry > 30

    def test_no_expiry_date(self):
        result = validate_expiry(None)
        assert result.is_expired is False

    def test_invalid_date_format(self):
        result = validate_expiry("not-a-date")
        assert result.is_expired is False
