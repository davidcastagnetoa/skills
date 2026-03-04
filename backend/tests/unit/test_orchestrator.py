"""Tests for the pipeline orchestrator module."""

import asyncio
import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from modules.orchestrator.models import (
    PhaseResult,
    PipelinePhase,
    PipelineResult,
    SessionProgress,
)
from modules.orchestrator.progress import ProgressTracker
from modules.orchestrator.service import PipelineOrchestrator


# ── Helpers ──────────────────────────────────────────────────────────

def _make_b64_image(width: int = 100, height: int = 100) -> str:
    """Create a minimal valid JPEG as base64."""
    import cv2

    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (128, 128, 128)
    _, buf = cv2.imencode(".jpg", img)
    return base64.b64encode(buf.tobytes()).decode()


def _make_mock_capture(valid: bool = True):
    svc = MagicMock()
    result = MagicMock()
    result.is_valid = valid
    result.quality_score = 0.9 if valid else 0.2
    result.issues = [] if valid else [MagicMock(description="Image too dark")]
    svc.validate.return_value = result
    return svc


def _make_mock_liveness(score: float = 0.85, is_live: bool = True):
    svc = MagicMock()
    result = MagicMock()
    result.liveness_score = score
    result.is_live = is_live
    result.attack_type_detected = MagicMock(value="none")
    svc.analyze.return_value = result
    return svc


def _make_mock_doc_processing(forgery: float = 0.1):
    svc = MagicMock()
    result = MagicMock()
    result.forgery_score = forgery
    result.detected_anomalies = []
    result.face_region = b"\x00" * 100
    result.processed_image = b"\x00" * 200
    svc.process.return_value = result
    return svc


def _make_mock_ocr(consistency: float = 0.95):
    svc = MagicMock()
    result = MagicMock()
    result.data_consistency_score = consistency
    result.is_expired = False
    result.mrz_valid = True
    result.fields = MagicMock(
        document_number="ABC123456",
        date_of_birth="1990-01-01",
        nationality="ESP",
    )
    svc.extract.return_value = result
    return svc


def _make_mock_face_match(similarity: float = 0.92):
    svc = MagicMock()
    result = MagicMock()
    result.similarity_score = similarity
    result.decision = MagicMock(value="match")
    svc.compare.return_value = result
    return svc


def _make_mock_antifraud(fraud_score: float = 0.1):
    svc = AsyncMock()
    result = MagicMock()
    result.fraud_score = fraud_score
    result.risk_flags = []
    result.recommended_action = MagicMock(value="approve")
    svc.analyze.return_value = result
    return svc


def _make_mock_decision(status: str = "VERIFIED", score: float = 0.92):
    svc = AsyncMock()
    result = MagicMock()
    result.status = MagicMock(value=status)
    result.confidence_score = score
    result.reasons = [MagicMock(message="All checks passed")]
    svc.decide.return_value = result
    return svc


def _make_mock_audit():
    svc = AsyncMock()
    svc.log_event = AsyncMock()
    svc.log_session_complete = AsyncMock(return_value="abc123hash")
    svc.log_error = AsyncMock()
    return svc


def _make_mock_progress():
    tracker = AsyncMock()
    tracker.start = AsyncMock()
    tracker.update = AsyncMock()
    tracker.complete_phase = AsyncMock()
    tracker.finish = AsyncMock()
    return tracker


def _make_orchestrator(**overrides):
    defaults = {
        "capture_validator": _make_mock_capture(),
        "liveness_service": _make_mock_liveness(),
        "doc_processing_service": _make_mock_doc_processing(),
        "ocr_service": _make_mock_ocr(),
        "face_match_service": _make_mock_face_match(),
        "antifraud_service": _make_mock_antifraud(),
        "decision_service": _make_mock_decision(),
        "audit_service": _make_mock_audit(),
        "progress_tracker": _make_mock_progress(),
    }
    defaults.update(overrides)
    return PipelineOrchestrator(**defaults)


# ── Models Tests ─────────────────────────────────────────────────────

class TestOrchestratorModels:
    def test_pipeline_phases(self):
        assert PipelinePhase.CAPTURE_VALIDATION.value == "capture_validation"
        assert PipelinePhase.DECISION.value == "decision"
        assert len(PipelinePhase) == 7

    def test_phase_result(self):
        pr = PhaseResult(phase=PipelinePhase.LIVENESS, score=0.85)
        assert pr.success is True
        assert pr.score == 0.85

    def test_session_progress(self):
        sp = SessionProgress(session_id="s1")
        assert sp.phases_completed == []
        assert sp.current_phase is None

    def test_pipeline_result(self):
        pr = PipelineResult(
            session_id="s1",
            status="VERIFIED",
            confidence_score=0.92,
        )
        assert pr.integrity_hash is None


# ── Progress Tracker Tests ───────────────────────────────────────────

class TestProgressTracker:
    def test_no_redis_noop(self):
        tracker = ProgressTracker(redis_client=None)
        # Should not raise
        asyncio.get_event_loop().run_until_complete(tracker.start("s1"))
        asyncio.get_event_loop().run_until_complete(
            tracker.update("s1", PipelinePhase.LIVENESS)
        )

    @pytest.mark.asyncio
    async def test_start_sets_key(self):
        mock_redis = AsyncMock()
        tracker = ProgressTracker(redis_client=mock_redis)
        await tracker.start("sess-1")
        mock_redis.setex.assert_called_once()
        key = mock_redis.setex.call_args[0][0]
        assert key == "progress:sess-1"

    @pytest.mark.asyncio
    async def test_get_returns_none_without_redis(self):
        tracker = ProgressTracker(redis_client=None)
        result = await tracker.get("sess-1")
        assert result is None


# ── Pipeline Orchestrator Tests ──────────────────────────────────────

class TestPipelineOrchestrator:
    @pytest.mark.asyncio
    async def test_successful_pipeline(self):
        orch = _make_orchestrator()
        selfie_b64 = _make_b64_image()
        doc_b64 = _make_b64_image()

        result = await orch.run("sess-1", selfie_b64, doc_b64)

        assert result.session_id == "sess-1"
        assert result.status == "VERIFIED"
        assert result.confidence_score > 0
        assert result.integrity_hash == "abc123hash"
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_capture_validation_failure_rejects(self):
        orch = _make_orchestrator(capture_validator=_make_mock_capture(valid=False))
        result = await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        assert result.status == "REJECTED"
        assert any("dark" in r.lower() for r in result.reasons)

    @pytest.mark.asyncio
    async def test_doc_processing_failure_rejects(self):
        mock_doc = MagicMock()
        mock_doc.process.side_effect = RuntimeError("Document unreadable")
        orch = _make_orchestrator(doc_processing_service=mock_doc)

        result = await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        assert result.status == "REJECTED"

    @pytest.mark.asyncio
    async def test_liveness_failure_degrades_gracefully(self):
        mock_liveness = MagicMock()
        mock_liveness.analyze.side_effect = RuntimeError("Model load failed")
        orch = _make_orchestrator(liveness_service=mock_liveness)

        result = await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        # Should still complete (liveness failure is non-fatal)
        assert result.status in ("VERIFIED", "MANUAL_REVIEW", "REJECTED")
        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_face_match_failure_degrades_gracefully(self):
        mock_face = MagicMock()
        mock_face.compare.side_effect = RuntimeError("Face not found")
        orch = _make_orchestrator(face_match_service=mock_face)

        result = await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        assert result.status in ("VERIFIED", "MANUAL_REVIEW", "REJECTED")

    @pytest.mark.asyncio
    async def test_ocr_failure_continues_with_penalty(self):
        mock_ocr = MagicMock()
        mock_ocr.extract.side_effect = RuntimeError("OCR engine unavailable")
        orch = _make_orchestrator(ocr_service=mock_ocr)

        result = await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        # Pipeline completes even with OCR failure
        assert result.status in ("VERIFIED", "MANUAL_REVIEW", "REJECTED")

    @pytest.mark.asyncio
    async def test_timeout_returns_error(self):
        async def slow_analyze(*args, **kwargs):
            await asyncio.sleep(10)
            return MagicMock(fraud_score=0.0, risk_flags=[], recommended_action=MagicMock(value="approve"))

        mock_antifraud = AsyncMock()
        mock_antifraud.analyze = slow_analyze
        orch = _make_orchestrator(antifraud_service=mock_antifraud, timeout=0.1)

        result = await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        assert result.status == "ERROR"
        assert any("timeout" in r.lower() for r in result.reasons)

    @pytest.mark.asyncio
    async def test_audit_events_logged(self):
        audit = _make_mock_audit()
        orch = _make_orchestrator(audit_service=audit)

        await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        # Should have logged: session_created, capture_validated, liveness, doc, face, ocr, antifraud, decision
        assert audit.log_event.call_count >= 7
        audit.log_session_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_progress_tracked(self):
        progress = _make_mock_progress()
        orch = _make_orchestrator(progress_tracker=progress)

        await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        progress.start.assert_called_once_with("sess-1")
        progress.finish.assert_called_once_with("sess-1")
        assert progress.complete_phase.call_count >= 5  # all phases

    @pytest.mark.asyncio
    async def test_module_scores_collected(self):
        orch = _make_orchestrator()
        result = await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        assert "liveness_score" in result.module_scores
        assert "face_match_score" in result.module_scores
        assert "document_integrity_score" in result.module_scores
        assert "ocr_consistency_score" in result.module_scores
        assert "antifraud_score" in result.module_scores

    @pytest.mark.asyncio
    async def test_no_face_in_document(self):
        mock_doc = MagicMock()
        result_obj = MagicMock()
        result_obj.forgery_score = 0.1
        result_obj.detected_anomalies = []
        result_obj.face_region = None  # No face found
        result_obj.processed_image = b"\x00"
        mock_doc.process.return_value = result_obj
        orch = _make_orchestrator(doc_processing_service=mock_doc)

        result = await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        # Pipeline should still complete
        assert result.status in ("VERIFIED", "MANUAL_REVIEW", "REJECTED")

    @pytest.mark.asyncio
    async def test_phase_results_tracked(self):
        orch = _make_orchestrator()
        result = await orch.run("sess-1", _make_b64_image(), _make_b64_image())

        phases = [pr.phase for pr in result.phase_results]
        assert PipelinePhase.CAPTURE_VALIDATION in phases
        assert PipelinePhase.LIVENESS in phases
        assert PipelinePhase.DOC_PROCESSING in phases
        assert PipelinePhase.FACE_MATCH in phases
        assert PipelinePhase.OCR in phases
        assert PipelinePhase.ANTIFRAUD in phases
        assert PipelinePhase.DECISION in phases


# ── Score Collection Tests ───────────────────────────────────────────

class TestScoreCollection:
    def test_all_successful(self):
        scores = PipelineOrchestrator._collect_scores(
            PhaseResult(phase=PipelinePhase.LIVENESS, score=0.9),
            PhaseResult(phase=PipelinePhase.DOC_PROCESSING, score=0.85),
            PhaseResult(phase=PipelinePhase.FACE_MATCH, score=0.95),
            PhaseResult(phase=PipelinePhase.OCR, score=0.88),
            PhaseResult(phase=PipelinePhase.ANTIFRAUD, score=0.05),
        )
        assert scores["liveness_score"] == 0.9
        assert scores["face_match_score"] == 0.95

    def test_liveness_failure_penalty(self):
        scores = PipelineOrchestrator._collect_scores(
            PhaseResult(phase=PipelinePhase.LIVENESS, success=False, score=0.0),
            PhaseResult(phase=PipelinePhase.DOC_PROCESSING, score=0.85),
            PhaseResult(phase=PipelinePhase.FACE_MATCH, score=0.95),
            PhaseResult(phase=PipelinePhase.OCR, score=0.88),
            PhaseResult(phase=PipelinePhase.ANTIFRAUD, score=0.05),
        )
        assert scores["liveness_score"] == 0.3  # penalty

    def test_face_match_failure_penalty(self):
        scores = PipelineOrchestrator._collect_scores(
            PhaseResult(phase=PipelinePhase.LIVENESS, score=0.9),
            PhaseResult(phase=PipelinePhase.DOC_PROCESSING, score=0.85),
            PhaseResult(phase=PipelinePhase.FACE_MATCH, success=False, score=0.0),
            PhaseResult(phase=PipelinePhase.OCR, score=0.88),
            PhaseResult(phase=PipelinePhase.ANTIFRAUD, score=0.05),
        )
        assert scores["face_match_score"] == 0.3

    def test_ocr_failure_soft_penalty(self):
        scores = PipelineOrchestrator._collect_scores(
            PhaseResult(phase=PipelinePhase.LIVENESS, score=0.9),
            PhaseResult(phase=PipelinePhase.DOC_PROCESSING, score=0.85),
            PhaseResult(phase=PipelinePhase.FACE_MATCH, score=0.95),
            PhaseResult(phase=PipelinePhase.OCR, success=False, score=0.0),
            PhaseResult(phase=PipelinePhase.ANTIFRAUD, score=0.05),
        )
        assert scores["ocr_consistency_score"] == 0.5  # softer penalty
