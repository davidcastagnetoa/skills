"""Unit tests for the antifraud module."""

from datetime import date

import numpy as np
import pytest

from modules.antifraud.age_consistency import calculate_age_from_dob, check_age_consistency
from modules.antifraud.geo_check import GeoLocationChecker, VPNProxyDetector
from modules.antifraud.models import (
    AntifraudResult,
    BlacklistCheckResult,
    GeoCheckResult,
    MultiAttemptResult,
    RecommendedAction,
    RiskFlag,
    RiskLevel,
)


class TestModels:
    def test_risk_flag(self):
        f = RiskFlag(code="test", message="Test flag", level=RiskLevel.HIGH, score_impact=0.5)
        assert f.level == RiskLevel.HIGH

    def test_antifraud_result_default(self):
        r = AntifraudResult()
        assert r.fraud_score == 0.0
        assert r.recommended_action == RecommendedAction.ALLOW

    def test_blacklist_result(self):
        r = BlacklistCheckResult(is_blacklisted=True, reason="stolen")
        assert r.is_blacklisted is True

    def test_multi_attempt_result(self):
        r = MultiAttemptResult(is_suspicious=True, attempts_count=5)
        assert r.is_suspicious is True
        assert r.attempts_count == 5


class TestGeoLocation:
    def test_no_reader(self):
        checker = GeoLocationChecker(geoip_reader=None)
        result = checker.check("1.2.3.4", "ESP")
        assert result.ip_country is None

    def test_no_ip(self):
        checker = GeoLocationChecker()
        result = checker.check(None, "ESP")
        assert result.is_discrepant is False

    def test_no_nationality(self):
        checker = GeoLocationChecker()
        result = checker.check("1.2.3.4", None)
        assert result.is_discrepant is False


class TestVPNDetector:
    def test_no_reader(self):
        detector = VPNProxyDetector(anonymous_ip_reader=None)
        result = detector.check("1.2.3.4")
        assert result.is_vpn is False
        assert result.is_tor is False

    def test_no_ip(self):
        detector = VPNProxyDetector()
        result = detector.check(None)
        assert result.is_vpn is False


class TestAgeConsistency:
    def test_calculate_age_valid(self):
        today = date.today()
        dob = f"{today.year - 30}-01-15"
        age = calculate_age_from_dob(dob)
        assert age in (29, 30)

    def test_calculate_age_none(self):
        assert calculate_age_from_dob(None) is None

    def test_calculate_age_invalid(self):
        assert calculate_age_from_dob("not-a-date") is None

    def test_check_no_face(self):
        result = check_age_consistency(None, "1990-01-01")
        assert result.document_age is not None
        assert result.estimated_age is None

    def test_check_no_dob(self):
        face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        result = check_age_consistency(face, None)
        assert result.document_age is None

    def test_check_no_model(self):
        face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        result = check_age_consistency(face, "1990-01-01", age_model_session=None)
        assert result.estimated_age is None
        assert result.is_suspicious is False
