"""PII anonymizer for audit logs.

Detects and masks personally identifiable information before
writing to audit logs, ensuring GDPR/LOPD compliance.
"""

import re

import structlog

logger = structlog.get_logger()

# Patterns for PII detection
_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"\+?\d[\d\s\-]{7,15}"),
    "document_number": re.compile(r"\b[A-Z]{0,3}\d{6,12}\b"),
}


def mask_name(name: str) -> str:
    """Mask a name: 'Juan Garcia' → 'J*** G***'."""
    if not name:
        return ""
    parts = name.split()
    masked = []
    for part in parts:
        if len(part) <= 1:
            masked.append(part)
        else:
            masked.append(part[0] + "***")
    return " ".join(masked)


def mask_document_number(doc_num: str) -> str:
    """Mask a document number: 'ABC12345678' → 'ABC****5678'."""
    if not doc_num or len(doc_num) < 4:
        return "****"
    visible_end = min(4, len(doc_num) // 3)
    prefix_len = max(0, len(doc_num) - visible_end - 4)
    prefix = doc_num[:prefix_len] if prefix_len > 0 else ""
    return prefix + "****" + doc_num[-visible_end:]


def mask_date(date_str: str) -> str:
    """Mask a date: '1990-03-15' → '1990-**-**'."""
    if not date_str or len(date_str) < 10:
        return "****-**-**"
    return date_str[:4] + "-**-**"


def anonymize_data(data: dict) -> dict:
    """Anonymize PII fields in a data dictionary.

    Recognizes and masks common PII fields by key name.
    """
    anonymized = {}
    pii_keys = {
        "full_name", "name", "surname", "given_names",
        "document_number", "doc_number", "personal_number",
        "date_of_birth", "dob",
        "email", "phone", "ip_address",
    }

    for key, value in data.items():
        if not isinstance(value, str):
            if isinstance(value, dict):
                anonymized[key] = anonymize_data(value)
            else:
                anonymized[key] = value
            continue

        key_lower = key.lower()

        if key_lower in ("full_name", "name", "surname", "given_names"):
            anonymized[key] = mask_name(value)
        elif key_lower in ("document_number", "doc_number", "personal_number"):
            anonymized[key] = mask_document_number(value)
        elif key_lower in ("date_of_birth", "dob"):
            anonymized[key] = mask_date(value)
        elif key_lower == "ip_address":
            # Mask last octet: 192.168.1.100 → 192.168.1.***
            parts = value.split(".")
            if len(parts) == 4:
                anonymized[key] = ".".join(parts[:3]) + ".***"
            else:
                anonymized[key] = "***"
        elif key_lower in ("email",):
            # mask@example.com → m***@e***.com
            at_idx = value.find("@")
            if at_idx > 0:
                anonymized[key] = value[0] + "***@" + value[at_idx + 1:at_idx + 2] + "***"
            else:
                anonymized[key] = "***"
        else:
            anonymized[key] = value

    return anonymized
