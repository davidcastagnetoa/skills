"""Unit tests for the liveness detection module."""

import numpy as np
import pytest

from modules.liveness.detectors.challenges import (
    detect_blink,
    detect_head_turn,
    detect_smile,
    generate_challenge_sequence,
    validate_response_timing,
)
from modules.liveness.detectors.depth import analyze_depth_variation, estimate_depth
from modules.liveness.detectors.optical_flow import analyze_optical_flow, compute_optical_flow
from modules.liveness.detectors.texture import analyze_texture
from modules.liveness.models import (
    ActiveLivenessResult,
    AttackType,
    ChallengeResult,
    ChallengeType,
    LivenessResult,
    PassiveLivenessResult,
)
from modules.liveness.service import LivenessService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_face_frame(w: int = 200, h: int = 200, intensity: int = 128) -> np.ndarray:
    """Create a synthetic BGR face-like image."""
    img = np.full((h, w, 3), intensity, dtype=np.uint8)
    # Add some texture
    noise = np.random.randint(0, 30, (h, w, 3), dtype=np.uint8)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img


def _make_moving_frames(n: int = 5) -> list[np.ndarray]:
    """Create frames with slight shifts to simulate movement."""
    base = _make_face_frame(200, 200)
    frames = [base]
    for i in range(1, n):
        shifted = np.roll(base, i * 3, axis=1)  # Shift horizontally
        frames.append(shifted)
    return frames


def _make_static_frames(n: int = 5) -> list[np.ndarray]:
    """Create identical frames (simulating a static photo)."""
    frame = _make_face_frame(200, 200)
    return [frame.copy() for _ in range(n)]


def _make_landmarks(n_points: int = 468) -> np.ndarray:
    """Create fake facial landmarks array."""
    return np.random.rand(n_points, 3).astype(np.float32) * 200


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestModels:
    def test_attack_type_enum(self):
        assert AttackType.NONE.value == "none"
        assert AttackType.DEEPFAKE.value == "deepfake"

    def test_challenge_type_enum(self):
        assert ChallengeType.BLINK.value == "blink"
        assert len(list(ChallengeType)) == 5

    def test_liveness_result_default(self):
        r = LivenessResult()
        assert r.is_live is False
        assert r.liveness_score == 0.0
        assert r.attack_type_detected == AttackType.NONE

    def test_passive_result_default(self):
        p = PassiveLivenessResult()
        assert p.combined_score == 0.0

    def test_active_result_default(self):
        a = ActiveLivenessResult()
        assert a.all_passed is False
        assert a.challenges == []


# ---------------------------------------------------------------------------
# Texture Analyzer
# ---------------------------------------------------------------------------


class TestTexture:
    def test_analyze_texture_with_frames(self):
        frames = [_make_face_frame() for _ in range(3)]
        score = analyze_texture(frames)
        assert 0.0 <= score <= 1.0

    def test_analyze_texture_empty(self):
        score = analyze_texture([])
        assert score == 0.0

    def test_analyze_texture_single_frame(self):
        score = analyze_texture([_make_face_frame()])
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Depth Estimator
# ---------------------------------------------------------------------------


class TestDepth:
    def test_depth_variation_flat(self):
        # Completely flat depth map → low score
        flat = np.ones((100, 100), dtype=np.float32)
        score = analyze_depth_variation(flat)
        assert score == 0.0

    def test_depth_variation_3d(self):
        # Depth map with variation → higher score
        depth = np.random.rand(100, 100).astype(np.float32) * 100
        score = analyze_depth_variation(depth)
        assert score > 0.0

    def test_depth_variation_none(self):
        score = analyze_depth_variation(None)
        assert score == 0.0

    def test_estimate_depth_no_model(self):
        img = _make_face_frame()
        score = estimate_depth(img, session=None)
        assert 0.0 <= score <= 1.0  # Falls back to Laplacian


# ---------------------------------------------------------------------------
# Optical Flow
# ---------------------------------------------------------------------------


class TestOpticalFlow:
    def test_optical_flow_moving_frames(self):
        frames = _make_moving_frames(5)
        score = analyze_optical_flow(frames)
        assert 0.0 <= score <= 1.0

    def test_optical_flow_static_frames(self):
        frames = _make_static_frames(5)
        score = analyze_optical_flow(frames)
        # Static → low score (suspicious)
        assert score <= 0.5

    def test_optical_flow_single_frame(self):
        score = analyze_optical_flow([_make_face_frame()])
        assert score == 0.0

    def test_optical_flow_empty(self):
        score = analyze_optical_flow([])
        assert score == 0.0

    def test_compute_optical_flow_returns_array(self):
        prev = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        curr = np.roll(prev, 5, axis=1)
        flow = compute_optical_flow(prev, curr)
        assert flow.shape == (100, 100, 2)


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------


class TestChallenges:
    def test_generate_sequence_default(self):
        seq = generate_challenge_sequence(3)
        assert len(seq) == 3
        # All unique
        assert len(set(seq)) == 3

    def test_generate_sequence_exclude(self):
        seq = generate_challenge_sequence(2, exclude=[ChallengeType.BLINK])
        assert ChallengeType.BLINK not in seq

    def test_generate_sequence_max(self):
        seq = generate_challenge_sequence(10)  # More than available
        assert len(seq) == len(list(ChallengeType))

    def test_detect_blink_insufficient_data(self):
        result = detect_blink([], [])
        assert result.passed is False
        assert result.challenge == ChallengeType.BLINK

    def test_detect_head_turn_insufficient_data(self):
        result = detect_head_turn([], [], ChallengeType.TURN_LEFT)
        assert result.passed is False

    def test_detect_smile_insufficient_data(self):
        result = detect_smile([], [])
        assert result.passed is False

    def test_validate_response_timing_valid(self):
        results = [
            ChallengeResult(challenge=ChallengeType.BLINK, passed=True, response_time_ms=1000),
            ChallengeResult(challenge=ChallengeType.SMILE, passed=True, response_time_ms=2000),
        ]
        assert validate_response_timing(results) is True

    def test_validate_response_timing_too_fast(self):
        results = [
            ChallengeResult(challenge=ChallengeType.BLINK, passed=True, response_time_ms=50),
        ]
        assert validate_response_timing(results) is False

    def test_validate_response_timing_too_slow(self):
        results = [
            ChallengeResult(challenge=ChallengeType.BLINK, passed=True, response_time_ms=15000),
        ]
        assert validate_response_timing(results) is False


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TestLivenessService:
    def test_passive_only(self):
        svc = LivenessService()
        frames = _make_moving_frames(5)
        result = svc.analyze(frames)
        assert isinstance(result, LivenessResult)
        assert result.processing_time_ms >= 0
        assert 0.0 <= result.liveness_score <= 1.0

    def test_passive_empty_frames(self):
        svc = LivenessService()
        result = svc.analyze([])
        assert result.is_live is False
        assert result.liveness_score == 0.0

    def test_generate_challenges(self):
        svc = LivenessService()
        challenges = svc.generate_challenges(3)
        assert len(challenges) == 3

    def test_classify_attack_live(self):
        passive = PassiveLivenessResult(combined_score=0.9)
        result = LivenessService._classify_attack(passive, is_live=True)
        assert result == AttackType.NONE

    def test_classify_attack_photo(self):
        passive = PassiveLivenessResult(
            texture_score=0.1,  # Lowest → photo
            depth_score=0.5,
            anti_spoof_score=0.5,
            deepfake_score=0.5,
            optical_flow_score=0.5,
        )
        result = LivenessService._classify_attack(passive, is_live=False)
        assert result == AttackType.PRINTED_PHOTO
