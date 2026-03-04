"""Pydantic schemas for the OCR module."""

from pydantic import BaseModel, Field


class TextRegion(BaseModel):
    """A detected text region with its content and confidence."""

    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[int] = Field(default_factory=list, description="[x1, y1, x2, y2]")


class MRZData(BaseModel):
    """Parsed Machine Readable Zone data (ICAO 9303)."""

    raw_lines: list[str] = Field(default_factory=list)
    document_type: str | None = None  # P (passport), ID, etc.
    country_code: str | None = None  # ISO 3166-1 alpha-3
    surname: str | None = None
    given_names: str | None = None
    document_number: str | None = None
    nationality: str | None = None
    date_of_birth: str | None = None  # YYMMDD
    sex: str | None = None  # M, F, X
    expiry_date: str | None = None  # YYMMDD
    personal_number: str | None = None
    is_valid: bool = False
    check_digit_results: dict[str, bool] = Field(default_factory=dict)


class ExtractedFields(BaseModel):
    """Normalized document fields extracted via OCR + MRZ."""

    full_name: str | None = None
    surname: str | None = None
    given_names: str | None = None
    document_number: str | None = None
    date_of_birth: str | None = None  # ISO 8601 (YYYY-MM-DD)
    expiry_date: str | None = None  # ISO 8601 (YYYY-MM-DD)
    nationality: str | None = None  # ISO 3166-1 alpha-3
    sex: str | None = None
    country_code: str | None = None
    document_type: str | None = None
    personal_number: str | None = None


class ConsistencyResult(BaseModel):
    """Result of cross-checking MRZ vs visual (VIZ) fields."""

    score: float = Field(ge=0.0, le=1.0, default=1.0)
    discrepancies: list[str] = Field(default_factory=list)


class ExpiryResult(BaseModel):
    """Document expiry validation result."""

    is_expired: bool = False
    days_until_expiry: int | None = None
    warning: str | None = None  # e.g., "expires_within_30_days"


class OCRResult(BaseModel):
    """Complete OCR extraction result."""

    fields: ExtractedFields = Field(default_factory=ExtractedFields)
    mrz_data: MRZData | None = None
    mrz_valid: bool = False
    text_regions: list[TextRegion] = Field(default_factory=list)
    data_consistency_score: float = Field(ge=0.0, le=1.0, default=1.0)
    consistency_discrepancies: list[str] = Field(default_factory=list)
    is_expired: bool = False
    expiry_warning: str | None = None
    ocr_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    engine_used: str = "paddleocr"
    processing_time_ms: int = 0
