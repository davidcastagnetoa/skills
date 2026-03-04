"""Pipeline orchestrator — runs the full KYC verification pipeline.

Phases:
    0. Capture validation
    1. Parallel: liveness + doc_processing
    2. Parallel: face_match + OCR
    3. Sequential: antifraud
    4. Sequential: decision
"""

import asyncio
import base64
import time

import cv2
import numpy as np
import structlog

from modules.antifraud.service import AntifraudService
from modules.audit.models import AuditEventType
from modules.audit.service import AuditService
from modules.capture.service import CaptureValidationService
from modules.decision.service import DecisionService
from modules.doc_processing.service import DocProcessingService
from modules.face_match.service import FaceMatchService
from modules.liveness.service import LivenessService
from modules.ocr.service import OCRService
from modules.orchestrator.models import (
    PhaseResult,
    PipelinePhase,
    PipelineResult,
)
from modules.orchestrator.progress import ProgressTracker

logger = structlog.get_logger()

# Global pipeline timeout in seconds
_PIPELINE_TIMEOUT = 8


class PipelineOrchestrator:
    """Orchestrates the full identity verification pipeline.

    Handles:
    - Parallel execution of independent phases
    - Partial failure / graceful degradation
    - Progress tracking via Redis
    - Audit trail logging
    - Global 8-second timeout
    """

    def __init__(
        self,
        capture_validator: CaptureValidationService | None = None,
        liveness_service: LivenessService | None = None,
        doc_processing_service: DocProcessingService | None = None,
        ocr_service: OCRService | None = None,
        face_match_service: FaceMatchService | None = None,
        antifraud_service: AntifraudService | None = None,
        decision_service: DecisionService | None = None,
        audit_service: AuditService | None = None,
        progress_tracker: ProgressTracker | None = None,
        storage_service=None,
        timeout: float = _PIPELINE_TIMEOUT,
    ) -> None:
        self._capture = capture_validator or CaptureValidationService()
        self._liveness = liveness_service or LivenessService()
        self._doc_processing = doc_processing_service or DocProcessingService()
        self._ocr = ocr_service or OCRService()
        self._face_match = face_match_service or FaceMatchService()
        self._antifraud = antifraud_service or AntifraudService()
        self._decision = decision_service or DecisionService()
        self._audit = audit_service or AuditService()
        self._progress = progress_tracker or ProgressTracker()
        self._storage = storage_service
        self._timeout = timeout

    async def run(
        self,
        session_id: str,
        selfie_image_b64: str,
        document_image_b64: str,
        device_fingerprint: str | None = None,
        ip_address: str | None = None,
        selfie_frames_b64: list[str] | None = None,
    ) -> PipelineResult:
        """Execute the full verification pipeline.

        Args:
            session_id: Unique session identifier.
            selfie_image_b64: Base64-encoded selfie image.
            document_image_b64: Base64-encoded document image.
            device_fingerprint: Client device fingerprint.
            ip_address: Client IP address.
            selfie_frames_b64: Optional list of base64-encoded video frames.

        Returns:
            PipelineResult with final decision.
        """
        start = time.perf_counter()
        phase_results: list[PhaseResult] = []

        await self._audit.log_event(
            session_id, AuditEventType.SESSION_CREATED, {"ip": ip_address}
        )
        await self._progress.start(session_id)

        try:
            result = await asyncio.wait_for(
                self._run_pipeline(
                    session_id,
                    selfie_image_b64,
                    document_image_b64,
                    device_fingerprint,
                    ip_address,
                    selfie_frames_b64,
                    phase_results,
                ),
                timeout=self._timeout,
            )
            return result
        except asyncio.TimeoutError:
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.warning("pipeline.timeout", session_id=session_id, elapsed_ms=elapsed)
            await self._audit.log_error(
                session_id, TimeoutError(f"Pipeline timeout after {elapsed}ms")
            )
            return PipelineResult(
                session_id=session_id,
                status="ERROR",
                reasons=["Pipeline timeout exceeded"],
                phase_results=phase_results,
                processing_time_ms=elapsed,
            )
        except Exception as exc:
            elapsed = int((time.perf_counter() - start) * 1000)
            logger.exception("pipeline.error", session_id=session_id)
            await self._audit.log_error(session_id, exc)
            return PipelineResult(
                session_id=session_id,
                status="ERROR",
                reasons=[f"Pipeline error: {type(exc).__name__}"],
                phase_results=phase_results,
                processing_time_ms=elapsed,
            )
        finally:
            await self._progress.finish(session_id)

    async def _run_pipeline(
        self,
        session_id: str,
        selfie_image_b64: str,
        document_image_b64: str,
        device_fingerprint: str | None,
        ip_address: str | None,
        selfie_frames_b64: list[str] | None,
        phase_results: list[PhaseResult],
    ) -> PipelineResult:
        start = time.perf_counter()

        # Decode images
        selfie_bytes = base64.b64decode(selfie_image_b64)
        doc_bytes = base64.b64decode(document_image_b64)
        selfie_frames = self._decode_frames(selfie_frames_b64 or [selfie_image_b64])

        # Upload to storage (if available)
        if self._storage:
            try:
                self._storage.upload(
                    "selfies", f"{session_id}/selfie.jpg", selfie_bytes
                )
                self._storage.upload(
                    "documents", f"{session_id}/document.jpg", doc_bytes
                )
            except Exception:
                logger.warning("pipeline.storage_upload_failed", session_id=session_id)

        # ── Phase 0: Capture validation ────────────────────────────────
        await self._progress.update(session_id, PipelinePhase.CAPTURE_VALIDATION)
        capture_result = await self._run_capture_validation(
            session_id, selfie_bytes, phase_results
        )
        if not capture_result.success:
            elapsed = int((time.perf_counter() - start) * 1000)
            return PipelineResult(
                session_id=session_id,
                status="REJECTED",
                reasons=capture_result.details.get("issues", ["Capture validation failed"]),
                phase_results=phase_results,
                processing_time_ms=elapsed,
            )
        await self._progress.complete_phase(session_id, PipelinePhase.CAPTURE_VALIDATION)

        # ── Phase 1: Parallel — liveness + doc_processing ──────────────
        await self._progress.update(session_id, PipelinePhase.LIVENESS)
        liveness_coro = self._run_liveness(session_id, selfie_frames, phase_results)
        doc_coro = self._run_doc_processing(session_id, doc_bytes, phase_results)
        liveness_phase, doc_phase = await asyncio.gather(
            liveness_coro, doc_coro, return_exceptions=False
        )
        await self._progress.complete_phase(session_id, PipelinePhase.LIVENESS)
        await self._progress.complete_phase(session_id, PipelinePhase.DOC_PROCESSING)

        # Check doc_processing failure (REJECTED — critical)
        if not doc_phase.success and doc_phase.error:
            elapsed = int((time.perf_counter() - start) * 1000)
            return PipelineResult(
                session_id=session_id,
                status="REJECTED",
                reasons=["Document processing failed"],
                phase_results=phase_results,
                processing_time_ms=elapsed,
            )

        # ── Phase 2: Parallel — face_match + OCR ──────────────────────
        await self._progress.update(session_id, PipelinePhase.FACE_MATCH)
        doc_face_bytes = doc_phase.details.get("face_region")
        doc_processed_bytes = doc_phase.details.get("processed_image")

        face_coro = self._run_face_match(
            session_id, selfie_bytes, doc_face_bytes, phase_results
        )
        ocr_coro = self._run_ocr(
            session_id, doc_processed_bytes or doc_bytes, phase_results
        )
        face_phase, ocr_phase = await asyncio.gather(
            face_coro, ocr_coro, return_exceptions=False
        )
        await self._progress.complete_phase(session_id, PipelinePhase.FACE_MATCH)
        await self._progress.complete_phase(session_id, PipelinePhase.OCR)

        # ── Phase 3: Antifraud ─────────────────────────────────────────
        await self._progress.update(session_id, PipelinePhase.ANTIFRAUD)
        antifraud_phase = await self._run_antifraud(
            session_id,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            ocr_details=ocr_phase.details,
            selfie_frames=selfie_frames,
            phase_results=phase_results,
        )
        await self._progress.complete_phase(session_id, PipelinePhase.ANTIFRAUD)

        # ── Phase 4: Decision ──────────────────────────────────────────
        await self._progress.update(session_id, PipelinePhase.DECISION)
        module_scores = self._collect_scores(
            liveness_phase, doc_phase, face_phase, ocr_phase, antifraud_phase
        )
        decision_phase = await self._run_decision(
            session_id, module_scores, phase_results
        )
        await self._progress.complete_phase(session_id, PipelinePhase.DECISION)

        # ── Finalize ───────────────────────────────────────────────────
        elapsed = int((time.perf_counter() - start) * 1000)

        integrity_hash = await self._audit.log_session_complete(
            session_id,
            decision_phase.details.get("status", "ERROR"),
            decision_phase.score,
        )

        return PipelineResult(
            session_id=session_id,
            status=decision_phase.details.get("status", "ERROR"),
            confidence_score=decision_phase.score,
            reasons=decision_phase.details.get("reasons", []),
            module_scores=module_scores,
            phase_results=phase_results,
            processing_time_ms=elapsed,
            integrity_hash=integrity_hash,
        )

    # ── Phase runners ──────────────────────────────────────────────────

    async def _run_capture_validation(
        self, session_id: str, selfie_bytes: bytes, results: list[PhaseResult]
    ) -> PhaseResult:
        t0 = time.perf_counter()
        try:
            result = self._capture.validate(selfie_bytes)
            elapsed = int((time.perf_counter() - t0) * 1000)
            phase = PhaseResult(
                phase=PipelinePhase.CAPTURE_VALIDATION,
                success=result.is_valid,
                score=result.quality_score if hasattr(result, "quality_score") else (1.0 if result.is_valid else 0.0),
                processing_time_ms=elapsed,
                details={"issues": [i.description for i in result.issues] if hasattr(result, "issues") and result.issues else []},
            )
            await self._audit.log_event(
                session_id,
                AuditEventType.CAPTURE_VALIDATED,
                {"is_valid": result.is_valid, "score": phase.score},
            )
        except Exception as exc:
            elapsed = int((time.perf_counter() - t0) * 1000)
            phase = PhaseResult(
                phase=PipelinePhase.CAPTURE_VALIDATION,
                success=False,
                error=str(exc),
                processing_time_ms=elapsed,
            )
        results.append(phase)
        return phase

    async def _run_liveness(
        self, session_id: str, frames: list[np.ndarray], results: list[PhaseResult]
    ) -> PhaseResult:
        """Run liveness detection. Failure → MANUAL_REVIEW (non-fatal)."""
        t0 = time.perf_counter()
        try:
            result = self._liveness.analyze(frames)
            elapsed = int((time.perf_counter() - t0) * 1000)
            phase = PhaseResult(
                phase=PipelinePhase.LIVENESS,
                success=True,
                score=result.liveness_score,
                processing_time_ms=elapsed,
                details={
                    "is_live": result.is_live,
                    "attack_type": result.attack_type_detected.value,
                },
            )
            await self._audit.log_event(
                session_id,
                AuditEventType.LIVENESS_COMPLETED,
                {"score": result.liveness_score, "is_live": result.is_live},
            )
        except Exception as exc:
            elapsed = int((time.perf_counter() - t0) * 1000)
            logger.warning("pipeline.liveness_failed", session_id=session_id, error=str(exc))
            phase = PhaseResult(
                phase=PipelinePhase.LIVENESS,
                success=False,
                score=0.0,
                error=str(exc),
                processing_time_ms=elapsed,
            )
        results.append(phase)
        return phase

    async def _run_doc_processing(
        self, session_id: str, doc_bytes: bytes, results: list[PhaseResult]
    ) -> PhaseResult:
        """Run document processing. Failure → REJECTED (critical)."""
        t0 = time.perf_counter()
        try:
            result = self._doc_processing.process(doc_bytes)
            elapsed = int((time.perf_counter() - t0) * 1000)
            phase = PhaseResult(
                phase=PipelinePhase.DOC_PROCESSING,
                success=True,
                score=1.0 - result.forgery_score,  # invert: higher = better
                processing_time_ms=elapsed,
                details={
                    "forgery_score": result.forgery_score,
                    "anomalies": result.detected_anomalies,
                    "face_region": result.face_region,
                    "processed_image": result.processed_image,
                },
            )
            await self._audit.log_event(
                session_id,
                AuditEventType.DOC_PROCESSING_COMPLETED,
                {"forgery_score": result.forgery_score},
            )
        except Exception as exc:
            elapsed = int((time.perf_counter() - t0) * 1000)
            logger.error("pipeline.doc_processing_failed", session_id=session_id, error=str(exc))
            phase = PhaseResult(
                phase=PipelinePhase.DOC_PROCESSING,
                success=False,
                error=str(exc),
                processing_time_ms=elapsed,
            )
        results.append(phase)
        return phase

    async def _run_face_match(
        self,
        session_id: str,
        selfie_bytes: bytes,
        doc_face_bytes: bytes | None,
        results: list[PhaseResult],
    ) -> PhaseResult:
        """Run face matching. Failure → MANUAL_REVIEW (non-fatal)."""
        t0 = time.perf_counter()
        if doc_face_bytes is None:
            elapsed = int((time.perf_counter() - t0) * 1000)
            phase = PhaseResult(
                phase=PipelinePhase.FACE_MATCH,
                success=False,
                score=0.0,
                error="No face extracted from document",
                processing_time_ms=elapsed,
            )
            results.append(phase)
            return phase

        try:
            result = self._face_match.compare(selfie_bytes, doc_face_bytes)
            elapsed = int((time.perf_counter() - t0) * 1000)
            phase = PhaseResult(
                phase=PipelinePhase.FACE_MATCH,
                success=True,
                score=result.similarity_score,
                processing_time_ms=elapsed,
                details={
                    "decision": result.decision.value,
                    "similarity": result.similarity_score,
                },
            )
            await self._audit.log_event(
                session_id,
                AuditEventType.FACE_MATCH_COMPLETED,
                {"similarity": result.similarity_score, "decision": result.decision.value},
            )
        except Exception as exc:
            elapsed = int((time.perf_counter() - t0) * 1000)
            logger.warning("pipeline.face_match_failed", session_id=session_id, error=str(exc))
            phase = PhaseResult(
                phase=PipelinePhase.FACE_MATCH,
                success=False,
                score=0.0,
                error=str(exc),
                processing_time_ms=elapsed,
            )
        results.append(phase)
        return phase

    async def _run_ocr(
        self, session_id: str, doc_image_bytes: bytes, results: list[PhaseResult]
    ) -> PhaseResult:
        """Run OCR extraction. Failure → continue with penalty (non-fatal)."""
        t0 = time.perf_counter()
        try:
            result = self._ocr.extract(doc_image_bytes)
            elapsed = int((time.perf_counter() - t0) * 1000)
            phase = PhaseResult(
                phase=PipelinePhase.OCR,
                success=True,
                score=result.data_consistency_score,
                processing_time_ms=elapsed,
                details={
                    "consistency_score": result.data_consistency_score,
                    "is_expired": result.is_expired,
                    "mrz_valid": result.mrz_valid,
                    "document_number": result.fields.document_number,
                    "date_of_birth": result.fields.date_of_birth,
                    "nationality": result.fields.nationality,
                },
            )
            await self._audit.log_event(
                session_id,
                AuditEventType.OCR_COMPLETED,
                {
                    "consistency_score": result.data_consistency_score,
                    "document_number": result.fields.document_number,
                },
            )
        except Exception as exc:
            elapsed = int((time.perf_counter() - t0) * 1000)
            logger.warning("pipeline.ocr_failed", session_id=session_id, error=str(exc))
            phase = PhaseResult(
                phase=PipelinePhase.OCR,
                success=False,
                score=0.0,
                error=str(exc),
                processing_time_ms=elapsed,
                details={},
            )
        results.append(phase)
        return phase

    async def _run_antifraud(
        self,
        session_id: str,
        device_fingerprint: str | None,
        ip_address: str | None,
        ocr_details: dict,
        selfie_frames: list[np.ndarray],
        results: list[PhaseResult],
    ) -> PhaseResult:
        t0 = time.perf_counter()
        try:
            selfie_face = selfie_frames[0] if selfie_frames else None
            result = await self._antifraud.analyze(
                document_number=ocr_details.get("document_number"),
                device_fingerprint=device_fingerprint,
                ip_address=ip_address,
                document_nationality=ocr_details.get("nationality"),
                date_of_birth=ocr_details.get("date_of_birth"),
                selfie_face=selfie_face,
            )
            elapsed = int((time.perf_counter() - t0) * 1000)
            phase = PhaseResult(
                phase=PipelinePhase.ANTIFRAUD,
                success=True,
                score=result.fraud_score,
                processing_time_ms=elapsed,
                details={
                    "fraud_score": result.fraud_score,
                    "flags": [f.code for f in result.risk_flags],
                    "action": result.recommended_action.value,
                },
            )
            await self._audit.log_event(
                session_id,
                AuditEventType.ANTIFRAUD_COMPLETED,
                {"fraud_score": result.fraud_score},
            )
        except Exception as exc:
            elapsed = int((time.perf_counter() - t0) * 1000)
            logger.warning("pipeline.antifraud_failed", session_id=session_id, error=str(exc))
            phase = PhaseResult(
                phase=PipelinePhase.ANTIFRAUD,
                success=True,
                score=0.0,
                processing_time_ms=elapsed,
            )
        results.append(phase)
        return phase

    async def _run_decision(
        self, session_id: str, module_scores: dict, results: list[PhaseResult]
    ) -> PhaseResult:
        t0 = time.perf_counter()
        try:
            result = await self._decision.decide(module_scores)
            elapsed = int((time.perf_counter() - t0) * 1000)
            phase = PhaseResult(
                phase=PipelinePhase.DECISION,
                success=True,
                score=result.confidence_score,
                processing_time_ms=elapsed,
                details={
                    "status": result.status.value,
                    "reasons": [r.message for r in result.reasons],
                },
            )
            await self._audit.log_event(
                session_id,
                AuditEventType.DECISION_MADE,
                {"status": result.status.value, "score": result.confidence_score},
            )
        except Exception as exc:
            elapsed = int((time.perf_counter() - t0) * 1000)
            logger.error("pipeline.decision_failed", session_id=session_id, error=str(exc))
            phase = PhaseResult(
                phase=PipelinePhase.DECISION,
                success=False,
                error=str(exc),
                processing_time_ms=elapsed,
                details={"status": "ERROR", "reasons": [str(exc)]},
            )
        results.append(phase)
        return phase

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _collect_scores(
        liveness: PhaseResult,
        doc: PhaseResult,
        face: PhaseResult,
        ocr: PhaseResult,
        antifraud: PhaseResult,
    ) -> dict:
        """Collect module scores for the decision engine.

        Handles partial failures with score penalties.
        """
        scores: dict[str, float] = {}

        # Liveness: failure → penalty score
        if liveness.success:
            scores["liveness_score"] = liveness.score
        else:
            scores["liveness_score"] = 0.3  # penalty — sends to MANUAL_REVIEW

        # Document integrity
        scores["document_integrity_score"] = doc.score if doc.success else 0.0

        # Face match: failure → penalty
        if face.success:
            scores["face_match_score"] = face.score
        else:
            scores["face_match_score"] = 0.3  # penalty

        # OCR: failure → penalty
        if ocr.success:
            scores["ocr_consistency_score"] = ocr.score
        else:
            scores["ocr_consistency_score"] = 0.5  # softer penalty

        # Antifraud
        scores["antifraud_score"] = antifraud.score if antifraud.success else 0.0

        return scores

    @staticmethod
    def _decode_frames(frames_b64: list[str]) -> list[np.ndarray]:
        """Decode base64-encoded frames to numpy arrays."""
        decoded: list[np.ndarray] = []
        for b64 in frames_b64:
            try:
                raw = base64.b64decode(b64)
                arr = np.frombuffer(raw, dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if img is not None:
                    decoded.append(img)
            except Exception:
                continue
        return decoded
