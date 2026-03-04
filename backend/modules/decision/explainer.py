"""Decision explainer — generates human-readable reasons for the verification decision."""

from modules.decision.models import DecisionReason, ScoreBreakdown, VerificationStatus


def explain_decision(
    scores: dict,
    breakdown: ScoreBreakdown,
    status: VerificationStatus,
) -> list[DecisionReason]:
    """Generate a list of human-readable reasons for the decision.

    Args:
        scores: Raw module scores.
        breakdown: Weighted score breakdown.
        status: Final verification status.

    Returns:
        List of DecisionReason with per-module explanations.
    """
    reasons: list[DecisionReason] = []

    # Liveness
    liveness = scores.get("liveness_score", 0.0)
    if liveness >= 0.8:
        reasons.append(DecisionReason(
            module="liveness",
            message="Liveness check passed with high confidence",
            impact="positive",
        ))
    elif liveness >= 0.5:
        reasons.append(DecisionReason(
            module="liveness",
            message="Liveness check passed with moderate confidence",
            impact="neutral",
        ))
    else:
        reasons.append(DecisionReason(
            module="liveness",
            message="Liveness check failed or returned low confidence",
            impact="negative",
        ))

    # Face match
    face_match = scores.get("face_match_score", 0.0)
    if face_match >= 0.85:
        reasons.append(DecisionReason(
            module="face_match",
            message=f"Face match score: {face_match:.2f} (high similarity)",
            impact="positive",
        ))
    elif face_match >= 0.70:
        reasons.append(DecisionReason(
            module="face_match",
            message=f"Face match score: {face_match:.2f} (moderate similarity, review recommended)",
            impact="neutral",
        ))
    else:
        reasons.append(DecisionReason(
            module="face_match",
            message=f"Face match score: {face_match:.2f} (low similarity)",
            impact="negative",
        ))

    # Document forgery
    forgery = scores.get("forgery_score", 0.0)
    if forgery < 0.3:
        reasons.append(DecisionReason(
            module="document",
            message="Document appears genuine",
            impact="positive",
        ))
    elif forgery < 0.7:
        reasons.append(DecisionReason(
            module="document",
            message=f"Document has some suspicious indicators (forgery score: {forgery:.2f})",
            impact="neutral",
        ))
    else:
        reasons.append(DecisionReason(
            module="document",
            message=f"Document manipulation suspected (forgery score: {forgery:.2f})",
            impact="negative",
        ))

    # OCR consistency
    ocr = scores.get("ocr_consistency_score", 1.0)
    if ocr >= 0.9:
        reasons.append(DecisionReason(
            module="ocr",
            message="Document data is internally consistent",
            impact="positive",
        ))
    elif ocr >= 0.7:
        reasons.append(DecisionReason(
            module="ocr",
            message="Minor data inconsistencies found in document",
            impact="neutral",
        ))
    else:
        reasons.append(DecisionReason(
            module="ocr",
            message="Significant data inconsistencies in document",
            impact="negative",
        ))

    # Antifraud
    fraud = scores.get("fraud_score", 0.0)
    if fraud > 0.5:
        reasons.append(DecisionReason(
            module="antifraud",
            message="Multiple fraud indicators detected",
            impact="negative",
        ))
    elif fraud > 0.2:
        reasons.append(DecisionReason(
            module="antifraud",
            message="Some fraud risk indicators present",
            impact="neutral",
        ))

    # Document expiry
    if scores.get("is_expired"):
        reasons.append(DecisionReason(
            module="document",
            message="Document is expired",
            impact="negative",
        ))

    # Blacklist
    if scores.get("is_blacklisted"):
        reasons.append(DecisionReason(
            module="antifraud",
            message="Document is in the blacklist",
            impact="negative",
        ))

    return reasons
