"""Active liveness challenge-response system.

Generates random challenges (blink, turn, smile) and validates
the user's response using facial landmarks from MediaPipe Face Mesh.
"""

import random
import time

import cv2
import numpy as np
import structlog

from modules.liveness.models import ChallengeResult, ChallengeType

logger = structlog.get_logger()

# EAR (Eye Aspect Ratio) threshold for blink detection
_EAR_THRESHOLD = 0.21
_BLINK_DURATION_MIN_MS = 80
_BLINK_DURATION_MAX_MS = 500

# Head pose thresholds (degrees)
_YAW_THRESHOLD = 15.0

# Smile detection threshold (mouth aspect ratio)
_SMILE_THRESHOLD = 0.35

# Response time limits
_MIN_RESPONSE_MS = 300   # Too fast = not human
_MAX_RESPONSE_MS = 10000  # Too slow = timeout

# MediaPipe Face Mesh landmark indices
_LEFT_EYE = [362, 385, 387, 263, 373, 380]
_RIGHT_EYE = [33, 160, 158, 133, 153, 144]
_MOUTH_OUTER = [61, 291, 13, 14]  # left, right, top, bottom
_NOSE_TIP = 1
_CHIN = 199
_LEFT_EYE_CORNER = 263
_RIGHT_EYE_CORNER = 33


def generate_challenge_sequence(n: int = 3, exclude: list[ChallengeType] | None = None) -> list[ChallengeType]:
    """Generate a random sequence of challenges.

    Args:
        n: Number of challenges (2-4).
        exclude: Challenge types to exclude from the pool.

    Returns:
        List of ChallengeType in random order.
    """
    pool = list(ChallengeType)
    if exclude:
        pool = [c for c in pool if c not in exclude]

    n = min(n, len(pool))
    sequence = random.sample(pool, n)

    logger.debug("challenges.sequence_generated", challenges=[c.value for c in sequence])
    return sequence


def _eye_aspect_ratio(landmarks: np.ndarray, eye_indices: list[int]) -> float:
    """Compute Eye Aspect Ratio (EAR) from landmarks.

    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    """
    p1 = landmarks[eye_indices[0]]
    p2 = landmarks[eye_indices[1]]
    p3 = landmarks[eye_indices[2]]
    p4 = landmarks[eye_indices[3]]
    p5 = landmarks[eye_indices[4]]
    p6 = landmarks[eye_indices[5]]

    vertical_1 = np.linalg.norm(p2 - p6)
    vertical_2 = np.linalg.norm(p3 - p5)
    horizontal = np.linalg.norm(p1 - p4)

    if horizontal < 1e-6:
        return 0.0

    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
    return float(ear)


def _estimate_yaw(landmarks: np.ndarray) -> float:
    """Estimate head yaw (left-right rotation) from landmarks.

    Uses the horizontal distance ratio between nose and eye corners.
    """
    nose = landmarks[_NOSE_TIP]
    left_eye = landmarks[_LEFT_EYE_CORNER]
    right_eye = landmarks[_RIGHT_EYE_CORNER]

    # Distance from nose to each eye corner
    d_left = np.linalg.norm(nose[:2] - left_eye[:2])
    d_right = np.linalg.norm(nose[:2] - right_eye[:2])

    total = d_left + d_right
    if total < 1e-6:
        return 0.0

    # Ratio: 0.5 = centered, <0.5 = turned right, >0.5 = turned left
    ratio = d_right / total
    # Convert to approximate degrees (linear approximation)
    yaw = (ratio - 0.5) * 90.0

    return float(yaw)


def _mouth_aspect_ratio(landmarks: np.ndarray) -> float:
    """Compute Mouth Aspect Ratio for smile detection."""
    left = landmarks[_MOUTH_OUTER[0]]
    right = landmarks[_MOUTH_OUTER[1]]
    top = landmarks[_MOUTH_OUTER[2]]
    bottom = landmarks[_MOUTH_OUTER[3]]

    horizontal = np.linalg.norm(left[:2] - right[:2])
    vertical = np.linalg.norm(top[:2] - bottom[:2])

    if horizontal < 1e-6:
        return 0.0

    return float(vertical / horizontal)


def detect_blink(
    landmarks_sequence: list[np.ndarray],
    timestamps_ms: list[int],
) -> ChallengeResult:
    """Detect a blink in a sequence of landmark frames.

    A valid blink: EAR drops below threshold for 80-500ms then recovers.
    """
    if len(landmarks_sequence) < 3:
        return ChallengeResult(challenge=ChallengeType.BLINK, passed=False)

    ear_values: list[float] = []
    for lms in landmarks_sequence:
        left_ear = _eye_aspect_ratio(lms, _LEFT_EYE)
        right_ear = _eye_aspect_ratio(lms, _RIGHT_EYE)
        ear_values.append((left_ear + right_ear) / 2.0)

    # Find blink pattern: high → low → high
    blink_detected = False
    blink_start = -1

    for i, ear in enumerate(ear_values):
        if ear < _EAR_THRESHOLD and blink_start == -1:
            blink_start = i
        elif ear >= _EAR_THRESHOLD and blink_start != -1:
            # Blink ended — check duration
            if i < len(timestamps_ms) and blink_start < len(timestamps_ms):
                duration = timestamps_ms[i] - timestamps_ms[blink_start]
                if _BLINK_DURATION_MIN_MS <= duration <= _BLINK_DURATION_MAX_MS:
                    blink_detected = True
                    break
            blink_start = -1

    response_time = timestamps_ms[-1] - timestamps_ms[0] if len(timestamps_ms) >= 2 else 0

    return ChallengeResult(
        challenge=ChallengeType.BLINK,
        passed=blink_detected,
        confidence=0.9 if blink_detected else 0.1,
        response_time_ms=response_time,
    )


def detect_head_turn(
    landmarks_sequence: list[np.ndarray],
    timestamps_ms: list[int],
    direction: ChallengeType,
) -> ChallengeResult:
    """Detect head turn in the specified direction."""
    if len(landmarks_sequence) < 3:
        return ChallengeResult(challenge=direction, passed=False)

    yaw_values = [_estimate_yaw(lms) for lms in landmarks_sequence]
    max_yaw = max(yaw_values)
    min_yaw = min(yaw_values)

    if direction == ChallengeType.TURN_LEFT:
        passed = max_yaw > _YAW_THRESHOLD
        confidence = min(max_yaw / 30.0, 1.0) if passed else 0.1
    elif direction == ChallengeType.TURN_RIGHT:
        passed = min_yaw < -_YAW_THRESHOLD
        confidence = min(abs(min_yaw) / 30.0, 1.0) if passed else 0.1
    else:
        return ChallengeResult(challenge=direction, passed=False)

    response_time = timestamps_ms[-1] - timestamps_ms[0] if len(timestamps_ms) >= 2 else 0

    return ChallengeResult(
        challenge=direction,
        passed=passed,
        confidence=round(confidence, 4),
        response_time_ms=response_time,
    )


def detect_smile(
    landmarks_sequence: list[np.ndarray],
    timestamps_ms: list[int],
) -> ChallengeResult:
    """Detect a smile in the landmark sequence."""
    if len(landmarks_sequence) < 2:
        return ChallengeResult(challenge=ChallengeType.SMILE, passed=False)

    mar_values = [_mouth_aspect_ratio(lms) for lms in landmarks_sequence]
    max_mar = max(mar_values)
    min_mar = min(mar_values)

    # A smile should show increased mouth aspect ratio
    smile_detected = max_mar > _SMILE_THRESHOLD and (max_mar - min_mar) > 0.05

    response_time = timestamps_ms[-1] - timestamps_ms[0] if len(timestamps_ms) >= 2 else 0

    return ChallengeResult(
        challenge=ChallengeType.SMILE,
        passed=smile_detected,
        confidence=0.85 if smile_detected else 0.1,
        response_time_ms=response_time,
    )


def validate_challenge(
    challenge: ChallengeType,
    landmarks_sequence: list[np.ndarray],
    timestamps_ms: list[int],
) -> ChallengeResult:
    """Validate a single challenge against the provided landmark sequence."""
    if challenge == ChallengeType.BLINK:
        return detect_blink(landmarks_sequence, timestamps_ms)
    elif challenge in (ChallengeType.TURN_LEFT, ChallengeType.TURN_RIGHT):
        return detect_head_turn(landmarks_sequence, timestamps_ms, challenge)
    elif challenge == ChallengeType.SMILE:
        return detect_smile(landmarks_sequence, timestamps_ms)
    elif challenge == ChallengeType.RAISE_EYEBROWS:
        # Similar to smile but with eyebrow landmarks — simplified
        return ChallengeResult(
            challenge=ChallengeType.RAISE_EYEBROWS,
            passed=False,
            confidence=0.0,
        )
    else:
        return ChallengeResult(challenge=challenge, passed=False)


def validate_response_timing(results: list[ChallengeResult]) -> bool:
    """Verify that response times are within human-plausible range."""
    for r in results:
        if r.response_time_ms < _MIN_RESPONSE_MS:
            logger.warning("challenges.response_too_fast", challenge=r.challenge, ms=r.response_time_ms)
            return False
        if r.response_time_ms > _MAX_RESPONSE_MS:
            logger.warning("challenges.response_too_slow", challenge=r.challenge, ms=r.response_time_ms)
            return False
    return True
