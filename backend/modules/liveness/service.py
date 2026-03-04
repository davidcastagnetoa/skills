"""Liveness detection service — combines passive and active checks."""

import time

import numpy as np
import structlog

from modules.liveness.detectors.anti_spoof import analyze_anti_spoof
from modules.liveness.detectors.challenges import (
    generate_challenge_sequence,
    validate_challenge,
    validate_response_timing,
)
from modules.liveness.detectors.deepfake import analyze_deepfake
from modules.liveness.detectors.depth import estimate_depth
from modules.liveness.detectors.optical_flow import analyze_optical_flow
from modules.liveness.detectors.texture import analyze_texture
from modules.liveness.models import (
    ActiveLivenessResult,
    AttackType,
    ChallengeResult,
    ChallengeType,
    LivenessResult,
    PassiveLivenessResult,
)

logger = structlog.get_logger()

# Passive liveness weights
_WEIGHTS = {
    "texture": 0.15,
    "depth": 0.15,
    "anti_spoof": 0.35,
    "deepfake": 0.20,
    "optical_flow": 0.15,
}

# Decision thresholds
_PASSIVE_THRESHOLD = 0.6
_ACTIVE_THRESHOLD = 0.7
_COMBINED_THRESHOLD = 0.65


class LivenessService:
    """Orchestrates passive and active liveness detection.

    Passive checks (run on all frames):
        - Texture analysis (LBP + Fourier)
        - Depth estimation (MiDaS or Laplacian fallback)
        - Anti-spoofing model (MiniFASNet)
        - Deepfake detection (XceptionNet)
        - Optical flow analysis (Farneback)

    Active checks (challenge-response):
        - Blink detection (EAR)
        - Head turn detection (yaw estimation)
        - Smile detection (mouth aspect ratio)
    """

    def __init__(
        self,
        anti_spoof_session=None,
        anti_spoof_session_large=None,
        depth_session=None,
        deepfake_session=None,
    ) -> None:
        self._anti_spoof_session = anti_spoof_session
        self._anti_spoof_session_large = anti_spoof_session_large
        self._depth_session = depth_session
        self._deepfake_session = deepfake_session

    def analyze_passive(self, frames: list[np.ndarray]) -> PassiveLivenessResult:
        """Run all passive liveness checks on the provided frames."""
        if not frames:
            return PassiveLivenessResult()

        texture_score = analyze_texture(frames)
        depth_score = estimate_depth(frames[0], self._depth_session)
        anti_spoof_score = analyze_anti_spoof(
            frames, self._anti_spoof_session, self._anti_spoof_session_large
        )
        deepfake_score = analyze_deepfake(frames, self._deepfake_session)
        optical_flow_score = analyze_optical_flow(frames)

        combined = (
            texture_score * _WEIGHTS["texture"]
            + depth_score * _WEIGHTS["depth"]
            + anti_spoof_score * _WEIGHTS["anti_spoof"]
            + deepfake_score * _WEIGHTS["deepfake"]
            + optical_flow_score * _WEIGHTS["optical_flow"]
        )

        return PassiveLivenessResult(
            texture_score=texture_score,
            depth_score=depth_score,
            anti_spoof_score=anti_spoof_score,
            deepfake_score=deepfake_score,
            optical_flow_score=optical_flow_score,
            combined_score=round(min(max(combined, 0.0), 1.0), 4),
        )

    def analyze_active(
        self,
        challenges: list[ChallengeType],
        landmarks_sequences: list[list[np.ndarray]],
        timestamps_sequences: list[list[int]],
    ) -> ActiveLivenessResult:
        """Validate active liveness challenges."""
        if not challenges:
            return ActiveLivenessResult()

        results: list[ChallengeResult] = []
        for i, challenge in enumerate(challenges):
            lms = landmarks_sequences[i] if i < len(landmarks_sequences) else []
            ts = timestamps_sequences[i] if i < len(timestamps_sequences) else []
            result = validate_challenge(challenge, lms, ts)
            results.append(result)

        all_passed = all(r.passed for r in results)
        timing_valid = validate_response_timing(results)

        if not timing_valid:
            all_passed = False

        avg_confidence = (
            sum(r.confidence for r in results) / len(results) if results else 0.0
        )

        return ActiveLivenessResult(
            challenges=results,
            all_passed=all_passed,
            score=round(avg_confidence, 4) if all_passed else round(avg_confidence * 0.5, 4),
        )

    def analyze(
        self,
        frames: list[np.ndarray],
        challenges: list[ChallengeType] | None = None,
        landmarks_sequences: list[list[np.ndarray]] | None = None,
        timestamps_sequences: list[list[int]] | None = None,
    ) -> LivenessResult:
        """Full liveness analysis combining passive and active checks."""
        start = time.perf_counter()

        # Passive analysis
        passive = self.analyze_passive(frames)

        # Active analysis (if challenges provided)
        active = ActiveLivenessResult()
        if challenges and landmarks_sequences and timestamps_sequences:
            active = self.analyze_active(
                challenges, landmarks_sequences, timestamps_sequences
            )

        # Combined decision
        has_active = bool(challenges)
        if has_active:
            combined_score = passive.combined_score * 0.5 + active.score * 0.5
            is_live = (
                passive.combined_score >= _PASSIVE_THRESHOLD
                and active.score >= _ACTIVE_THRESHOLD
                and combined_score >= _COMBINED_THRESHOLD
            )
        else:
            combined_score = passive.combined_score
            is_live = combined_score >= _PASSIVE_THRESHOLD

        # Detect attack type
        attack_type = self._classify_attack(passive, is_live)

        elapsed = int((time.perf_counter() - start) * 1000)

        logger.info(
            "liveness_service.complete",
            is_live=is_live,
            passive_score=passive.combined_score,
            active_score=active.score,
            combined_score=round(combined_score, 4),
            attack_type=attack_type.value,
            elapsed_ms=elapsed,
        )

        return LivenessResult(
            is_live=is_live,
            liveness_score=round(combined_score, 4),
            attack_type_detected=attack_type,
            passive=passive,
            active=active,
            processing_time_ms=elapsed,
        )

    def generate_challenges(self, n: int = 3) -> list[ChallengeType]:
        """Generate a random challenge sequence for the client."""
        return generate_challenge_sequence(n)

    @staticmethod
    def _classify_attack(passive: PassiveLivenessResult, is_live: bool) -> AttackType:
        """Classify the type of attack based on passive scores."""
        if is_live:
            return AttackType.NONE

        scores = {
            AttackType.PRINTED_PHOTO: passive.texture_score,
            AttackType.SCREEN_REPLAY: passive.optical_flow_score,
            AttackType.DEEPFAKE: passive.deepfake_score,
            AttackType.MASK_3D: passive.depth_score,
        }

        worst = min(scores, key=scores.get)
        if scores[worst] < 0.4:
            return worst

        return AttackType.UNKNOWN
