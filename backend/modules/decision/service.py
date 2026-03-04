"""Decision service — orchestrates hard rules, scoring, classification, and explanation."""

import time

import structlog

from modules.decision.explainer import explain_decision
from modules.decision.models import (
    DecisionResult,
    VerificationStatus,
)
from modules.decision.rules import (
    REVIEW_THRESHOLD,
    VERIFY_THRESHOLD,
    calculate_weighted_score,
    evaluate_hard_rules,
)

logger = structlog.get_logger()


class DecisionService:
    """Orchestrates the verification decision process.

    Pipeline:
        1. Evaluate hard reject rules (immediate REJECTED if triggered).
        2. Calculate weighted global score.
        3. Classify into VERIFIED / MANUAL_REVIEW / REJECTED.
        4. Generate human-readable explanations.
    """

    def __init__(self, redis_client=None) -> None:
        self._redis = redis_client

    async def decide(self, scores: dict) -> DecisionResult:
        """Make a verification decision based on module scores.

        Args:
            scores: Dict containing:
                - liveness_score (float 0-1)
                - face_match_score (float 0-1)
                - forgery_score (float 0-1)
                - ocr_consistency_score (float 0-1)
                - fraud_score (float 0-1)
                - is_expired (bool)
                - is_blacklisted (bool)
                - selfie_face_detected (bool)

        Returns:
            DecisionResult with status, confidence, reasons.
        """
        start = time.perf_counter()

        # 1. Hard rules
        hard_result = evaluate_hard_rules(scores)
        if hard_result.triggered:
            breakdown = calculate_weighted_score(scores, await self._get_weights())
            reasons = explain_decision(scores, breakdown, VerificationStatus.REJECTED)

            elapsed = int((time.perf_counter() - start) * 1000)
            logger.info(
                "decision.hard_reject",
                rule=hard_result.rule_code,
                elapsed_ms=elapsed,
            )

            return DecisionResult(
                status=VerificationStatus.REJECTED,
                confidence_score=breakdown.global_score,
                reasons=reasons,
                hard_rule=hard_result,
                score_breakdown=breakdown,
                processing_time_ms=elapsed,
            )

        # 2. Weighted score
        weights = await self._get_weights()
        breakdown = calculate_weighted_score(scores, weights)

        # 3. Classify
        if breakdown.global_score >= VERIFY_THRESHOLD:
            status = VerificationStatus.VERIFIED
        elif breakdown.global_score >= REVIEW_THRESHOLD:
            status = VerificationStatus.MANUAL_REVIEW
        else:
            status = VerificationStatus.REJECTED

        # 4. Explain
        reasons = explain_decision(scores, breakdown, status)

        elapsed = int((time.perf_counter() - start) * 1000)

        logger.info(
            "decision.complete",
            status=status.value,
            global_score=breakdown.global_score,
            elapsed_ms=elapsed,
        )

        return DecisionResult(
            status=status,
            confidence_score=breakdown.global_score,
            reasons=reasons,
            hard_rule=hard_result,
            score_breakdown=breakdown,
            processing_time_ms=elapsed,
        )

    async def _get_weights(self) -> dict[str, float] | None:
        """Load weights from Redis if available (runtime-configurable)."""
        if self._redis is None:
            return None

        try:
            import json

            raw = await self._redis.get("decision:weights")
            if raw:
                return json.loads(raw)
        except Exception:
            pass

        return None
