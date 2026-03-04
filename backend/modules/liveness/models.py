"""Pydantic schemas for the liveness detection module."""

from enum import Enum

from pydantic import BaseModel, Field


class AttackType(str, Enum):
    """Types of spoofing attacks detected."""

    NONE = "none"
    PRINTED_PHOTO = "printed_photo"
    SCREEN_REPLAY = "screen_replay"
    MASK_3D = "mask_3d"
    DEEPFAKE = "deepfake"
    VIDEO_REPLAY = "video_replay"
    UNKNOWN = "unknown"


class ChallengeType(str, Enum):
    """Active liveness challenge types."""

    BLINK = "blink"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    SMILE = "smile"
    RAISE_EYEBROWS = "raise_eyebrows"


class ChallengeResult(BaseModel):
    """Result of a single challenge."""

    challenge: ChallengeType
    passed: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    response_time_ms: int = 0


class PassiveLivenessResult(BaseModel):
    """Aggregated result of all passive liveness checks."""

    texture_score: float = Field(ge=0.0, le=1.0, default=0.0)
    depth_score: float = Field(ge=0.0, le=1.0, default=0.0)
    anti_spoof_score: float = Field(ge=0.0, le=1.0, default=0.0)
    deepfake_score: float = Field(ge=0.0, le=1.0, default=0.0)
    optical_flow_score: float = Field(ge=0.0, le=1.0, default=0.0)
    combined_score: float = Field(ge=0.0, le=1.0, default=0.0)


class ActiveLivenessResult(BaseModel):
    """Aggregated result of active (challenge-response) checks."""

    challenges: list[ChallengeResult] = Field(default_factory=list)
    all_passed: bool = False
    score: float = Field(ge=0.0, le=1.0, default=0.0)


class LivenessResult(BaseModel):
    """Complete liveness detection result."""

    is_live: bool = False
    liveness_score: float = Field(ge=0.0, le=1.0, default=0.0)
    attack_type_detected: AttackType = AttackType.NONE
    passive: PassiveLivenessResult = Field(default_factory=PassiveLivenessResult)
    active: ActiveLivenessResult = Field(default_factory=ActiveLivenessResult)
    processing_time_ms: int = 0
