"""Hard rule engine and weighted score aggregator for the decision module."""

import structlog

from modules.decision.models import HardRuleResult, ScoreBreakdown

logger = structlog.get_logger()

# Hard reject rules: if any trigger, decision is REJECTED immediately
HARD_REJECT_RULES = [
    {
        "code": "liveness_critical_fail",
        "field": "liveness_score",
        "operator": "lt",
        "threshold": 0.3,
        "reason": "Liveness check failed critically",
    },
    {
        "code": "face_match_critical_fail",
        "field": "face_match_score",
        "operator": "lt",
        "threshold": 0.5,
        "reason": "Face match below minimum threshold",
    },
    {
        "code": "document_expired",
        "field": "is_expired",
        "operator": "eq",
        "threshold": True,
        "reason": "Document is expired",
    },
    {
        "code": "document_blacklisted",
        "field": "is_blacklisted",
        "operator": "eq",
        "threshold": True,
        "reason": "Document is blacklisted",
    },
    {
        "code": "no_face_in_selfie",
        "field": "selfie_face_detected",
        "operator": "eq",
        "threshold": False,
        "reason": "No face detected in selfie",
    },
    {
        "code": "high_forgery_score",
        "field": "forgery_score",
        "operator": "gt",
        "threshold": 0.8,
        "reason": "Document manipulation detected",
    },
]

# Default weights for score aggregation (stored in Redis for runtime adjustment)
DEFAULT_WEIGHTS = {
    "liveness_score": 0.25,
    "face_match_score": 0.30,
    "document_integrity_score": 0.20,  # 1 - forgery_score
    "ocr_consistency_score": 0.10,
    "antifraud_score": 0.15,  # 1 - fraud_score
}

# Classification thresholds
VERIFY_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.60


def evaluate_hard_rules(scores: dict) -> HardRuleResult:
    """Evaluate hard reject rules against the provided scores.

    Args:
        scores: Dict with module scores and boolean flags.

    Returns:
        HardRuleResult — triggered=True if any rule fires.
    """
    for rule in HARD_REJECT_RULES:
        field = rule["field"]
        if field not in scores:
            continue

        value = scores[field]
        op = rule["operator"]
        threshold = rule["threshold"]

        triggered = False
        if op == "lt" and value < threshold:
            triggered = True
        elif op == "gt" and value > threshold:
            triggered = True
        elif op == "eq" and value == threshold:
            triggered = True

        if triggered:
            logger.info(
                "hard_rules.triggered",
                rule=rule["code"],
                field=field,
                value=value,
                threshold=threshold,
            )
            return HardRuleResult(
                triggered=True,
                rule_code=rule["code"],
                reason=rule["reason"],
            )

    return HardRuleResult(triggered=False)


def calculate_weighted_score(
    scores: dict,
    weights: dict[str, float] | None = None,
) -> ScoreBreakdown:
    """Calculate weighted global score from module scores.

    Args:
        scores: Dict with raw module scores.
        weights: Custom weights (uses DEFAULT_WEIGHTS if None).

    Returns:
        ScoreBreakdown with per-module weighted contributions.
    """
    w = weights or DEFAULT_WEIGHTS

    liveness = scores.get("liveness_score", 0.0)
    face_match = scores.get("face_match_score", 0.0)
    # Invert forgery: 0 forgery = 1.0 integrity
    forgery = scores.get("forgery_score", 0.0)
    doc_integrity = 1.0 - min(forgery, 1.0)
    ocr = scores.get("ocr_consistency_score", 1.0)
    # Invert fraud: 0 fraud = 1.0 clean
    fraud = scores.get("fraud_score", 0.0)
    antifraud = 1.0 - min(fraud, 1.0)

    breakdown = ScoreBreakdown(
        liveness_score=round(liveness, 4),
        liveness_weighted=round(liveness * w.get("liveness_score", 0.25), 4),
        face_match_score=round(face_match, 4),
        face_match_weighted=round(face_match * w.get("face_match_score", 0.30), 4),
        document_integrity_score=round(doc_integrity, 4),
        document_integrity_weighted=round(doc_integrity * w.get("document_integrity_score", 0.20), 4),
        ocr_consistency_score=round(ocr, 4),
        ocr_consistency_weighted=round(ocr * w.get("ocr_consistency_score", 0.10), 4),
        antifraud_score=round(antifraud, 4),
        antifraud_weighted=round(antifraud * w.get("antifraud_score", 0.15), 4),
    )

    breakdown.global_score = round(
        breakdown.liveness_weighted
        + breakdown.face_match_weighted
        + breakdown.document_integrity_weighted
        + breakdown.ocr_consistency_weighted
        + breakdown.antifraud_weighted,
        4,
    )

    return breakdown
