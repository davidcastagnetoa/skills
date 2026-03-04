"""Unit tests for the decision engine module."""

import pytest

from modules.decision.explainer import explain_decision
from modules.decision.models import (
    DecisionResult,
    ScoreBreakdown,
    VerificationStatus,
)
from modules.decision.rules import (
    REVIEW_THRESHOLD,
    VERIFY_THRESHOLD,
    calculate_weighted_score,
    evaluate_hard_rules,
)


class TestHardRules:
    def test_no_rules_triggered(self):
        scores = {
            "liveness_score": 0.9,
            "face_match_score": 0.9,
            "forgery_score": 0.1,
            "is_expired": False,
            "is_blacklisted": False,
            "selfie_face_detected": True,
        }
        result = evaluate_hard_rules(scores)
        assert result.triggered is False

    def test_liveness_critical_fail(self):
        scores = {"liveness_score": 0.1}
        result = evaluate_hard_rules(scores)
        assert result.triggered is True
        assert result.rule_code == "liveness_critical_fail"

    def test_face_match_critical_fail(self):
        scores = {"liveness_score": 0.9, "face_match_score": 0.3}
        result = evaluate_hard_rules(scores)
        assert result.triggered is True
        assert result.rule_code == "face_match_critical_fail"

    def test_document_expired(self):
        scores = {"liveness_score": 0.9, "face_match_score": 0.9, "is_expired": True}
        result = evaluate_hard_rules(scores)
        assert result.triggered is True
        assert result.rule_code == "document_expired"

    def test_document_blacklisted(self):
        scores = {
            "liveness_score": 0.9,
            "face_match_score": 0.9,
            "is_expired": False,
            "is_blacklisted": True,
        }
        result = evaluate_hard_rules(scores)
        assert result.triggered is True

    def test_no_face_detected(self):
        scores = {
            "liveness_score": 0.9,
            "face_match_score": 0.9,
            "is_expired": False,
            "is_blacklisted": False,
            "selfie_face_detected": False,
        }
        result = evaluate_hard_rules(scores)
        assert result.triggered is True

    def test_high_forgery(self):
        scores = {
            "liveness_score": 0.9,
            "face_match_score": 0.9,
            "is_expired": False,
            "is_blacklisted": False,
            "selfie_face_detected": True,
            "forgery_score": 0.9,
        }
        result = evaluate_hard_rules(scores)
        assert result.triggered is True


class TestWeightedScore:
    def test_perfect_scores(self):
        scores = {
            "liveness_score": 1.0,
            "face_match_score": 1.0,
            "forgery_score": 0.0,
            "ocr_consistency_score": 1.0,
            "fraud_score": 0.0,
        }
        breakdown = calculate_weighted_score(scores)
        assert breakdown.global_score == 1.0

    def test_zero_scores(self):
        scores = {
            "liveness_score": 0.0,
            "face_match_score": 0.0,
            "forgery_score": 1.0,
            "ocr_consistency_score": 0.0,
            "fraud_score": 1.0,
        }
        breakdown = calculate_weighted_score(scores)
        assert breakdown.global_score == 0.0

    def test_mixed_scores_verified(self):
        scores = {
            "liveness_score": 0.95,
            "face_match_score": 0.92,
            "forgery_score": 0.05,
            "ocr_consistency_score": 0.98,
            "fraud_score": 0.0,
        }
        breakdown = calculate_weighted_score(scores)
        assert breakdown.global_score >= VERIFY_THRESHOLD

    def test_mixed_scores_review(self):
        scores = {
            "liveness_score": 0.7,
            "face_match_score": 0.75,
            "forgery_score": 0.2,
            "ocr_consistency_score": 0.8,
            "fraud_score": 0.1,
        }
        breakdown = calculate_weighted_score(scores)
        assert REVIEW_THRESHOLD <= breakdown.global_score < VERIFY_THRESHOLD

    def test_forgery_inverted(self):
        # forgery_score of 0.0 should give document_integrity of 1.0
        scores = {"forgery_score": 0.0}
        breakdown = calculate_weighted_score(scores)
        assert breakdown.document_integrity_score == 1.0

    def test_fraud_inverted(self):
        scores = {"fraud_score": 1.0}
        breakdown = calculate_weighted_score(scores)
        assert breakdown.antifraud_score == 0.0

    def test_custom_weights(self):
        scores = {
            "liveness_score": 1.0,
            "face_match_score": 1.0,
            "forgery_score": 0.0,
            "ocr_consistency_score": 1.0,
            "fraud_score": 0.0,
        }
        weights = {
            "liveness_score": 0.5,
            "face_match_score": 0.5,
            "document_integrity_score": 0.0,
            "ocr_consistency_score": 0.0,
            "antifraud_score": 0.0,
        }
        breakdown = calculate_weighted_score(scores, weights)
        assert breakdown.global_score == 1.0


class TestExplainer:
    def test_positive_reasons(self):
        scores = {
            "liveness_score": 0.95,
            "face_match_score": 0.92,
            "forgery_score": 0.05,
            "ocr_consistency_score": 0.98,
            "fraud_score": 0.0,
        }
        breakdown = ScoreBreakdown(global_score=0.95)
        reasons = explain_decision(scores, breakdown, VerificationStatus.VERIFIED)
        positive = [r for r in reasons if r.impact == "positive"]
        assert len(positive) >= 3

    def test_negative_reasons(self):
        scores = {
            "liveness_score": 0.1,
            "face_match_score": 0.3,
            "forgery_score": 0.9,
            "ocr_consistency_score": 0.4,
            "fraud_score": 0.8,
            "is_expired": True,
            "is_blacklisted": True,
        }
        breakdown = ScoreBreakdown(global_score=0.1)
        reasons = explain_decision(scores, breakdown, VerificationStatus.REJECTED)
        negative = [r for r in reasons if r.impact == "negative"]
        assert len(negative) >= 4

    def test_all_modules_represented(self):
        scores = {
            "liveness_score": 0.5,
            "face_match_score": 0.5,
            "forgery_score": 0.5,
            "ocr_consistency_score": 0.5,
            "fraud_score": 0.5,
        }
        breakdown = ScoreBreakdown(global_score=0.5)
        reasons = explain_decision(scores, breakdown, VerificationStatus.MANUAL_REVIEW)
        modules = {r.module for r in reasons}
        assert "liveness" in modules
        assert "face_match" in modules
        assert "document" in modules


class TestModels:
    def test_decision_result_default(self):
        r = DecisionResult()
        assert r.status == VerificationStatus.REJECTED
        assert r.confidence_score == 0.0

    def test_verification_status_values(self):
        assert VerificationStatus.VERIFIED.value == "verified"
        assert VerificationStatus.REJECTED.value == "rejected"
        assert VerificationStatus.MANUAL_REVIEW.value == "manual_review"
