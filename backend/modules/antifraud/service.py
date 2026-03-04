"""Antifraud service — orchestrates all fraud detection checks."""

import time

import numpy as np
import structlog

from modules.antifraud.age_consistency import check_age_consistency
from modules.antifraud.blacklist import BlacklistChecker
from modules.antifraud.geo_check import GeoLocationChecker, VPNProxyDetector
from modules.antifraud.models import (
    AntifraudResult,
    RecommendedAction,
    RiskFlag,
    RiskLevel,
)
from modules.antifraud.multi_attempt import MultiAttemptDetector

logger = structlog.get_logger()


class AntifraudService:
    """Orchestrates all antifraud checks.

    Checks:
    1. Document blacklist
    2. Multi-attempt detection
    3. Geolocation consistency
    4. VPN/proxy/Tor detection
    5. Age consistency
    """

    def __init__(
        self,
        redis_client=None,
        db_session=None,
        age_model_session=None,
    ) -> None:
        self._blacklist = BlacklistChecker(redis_client, db_session)
        self._multi_attempt = MultiAttemptDetector(redis_client)
        self._geo_checker = GeoLocationChecker()
        self._vpn_detector = VPNProxyDetector()
        self._age_model_session = age_model_session

    async def analyze(
        self,
        document_number: str | None = None,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
        document_nationality: str | None = None,
        date_of_birth: str | None = None,
        selfie_face: np.ndarray | None = None,
    ) -> AntifraudResult:
        """Run all antifraud checks and aggregate results.

        Returns:
            AntifraudResult with fraud score and risk flags.
        """
        start = time.perf_counter()
        risk_flags: list[RiskFlag] = []

        # 1. Blacklist check
        blacklist = await self._blacklist.check(document_number)
        if blacklist.is_blacklisted:
            risk_flags.append(RiskFlag(
                code="document_blacklisted",
                message="Document number is in the blacklist",
                level=RiskLevel.CRITICAL,
                score_impact=1.0,
            ))

        # 2. Multi-attempt detection
        multi_attempt = await self._multi_attempt.check(
            device_fingerprint, ip_address, document_number
        )
        if multi_attempt.is_suspicious:
            risk_flags.append(RiskFlag(
                code="multi_attempt_suspicious",
                message=f"Suspicious activity: {multi_attempt.attempts_count} attempts, {multi_attempt.different_documents} documents",
                level=RiskLevel.HIGH,
                score_impact=0.4,
            ))

        # 3. Geolocation
        geo = self._geo_checker.check(ip_address, document_nationality)
        if geo.is_discrepant:
            risk_flags.append(RiskFlag(
                code="geo_discrepancy",
                message=f"IP country ({geo.ip_country}) differs from document ({geo.document_nationality})",
                level=RiskLevel.MEDIUM,
                score_impact=0.15,
            ))

        # 4. VPN/proxy/Tor
        vpn_result = self._vpn_detector.check(ip_address)
        if vpn_result.is_vpn or vpn_result.is_proxy or vpn_result.is_tor:
            level = RiskLevel.HIGH if vpn_result.is_tor else RiskLevel.MEDIUM
            risk_flags.append(RiskFlag(
                code="anonymous_connection",
                message="VPN/proxy/Tor connection detected",
                level=level,
                score_impact=0.2 if vpn_result.is_tor else 0.1,
            ))
            geo.is_vpn = vpn_result.is_vpn
            geo.is_proxy = vpn_result.is_proxy
            geo.is_tor = vpn_result.is_tor

        # 5. Age consistency
        age = check_age_consistency(selfie_face, date_of_birth, self._age_model_session)
        if age.is_suspicious:
            risk_flags.append(RiskFlag(
                code="age_discrepancy",
                message=f"Visual age ({age.estimated_age}) differs from document ({age.document_age}) by {age.discrepancy_years} years",
                level=RiskLevel.HIGH,
                score_impact=0.3,
            ))

        # Aggregate fraud score
        fraud_score = min(sum(f.score_impact for f in risk_flags), 1.0)

        # Determine recommended action
        if blacklist.is_blacklisted:
            action = RecommendedAction.REJECT
        elif fraud_score >= 0.5:
            action = RecommendedAction.REJECT
        elif fraud_score >= 0.2:
            action = RecommendedAction.REVIEW
        else:
            action = RecommendedAction.ALLOW

        elapsed = int((time.perf_counter() - start) * 1000)

        logger.info(
            "antifraud.complete",
            fraud_score=round(fraud_score, 4),
            action=action.value,
            n_flags=len(risk_flags),
            elapsed_ms=elapsed,
        )

        return AntifraudResult(
            fraud_score=round(fraud_score, 4),
            risk_flags=risk_flags,
            recommended_action=action,
            blacklist=blacklist,
            multi_attempt=multi_attempt,
            geo_check=geo,
            age_consistency=age,
            processing_time_ms=elapsed,
        )
