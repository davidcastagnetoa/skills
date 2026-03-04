"""Unit tests for ML Celery task registration and configuration."""

import pytest


class TestMLTaskRegistration:
    """Verify that ML tasks are properly registered with correct configuration."""

    def test_process_document_task_exists(self):
        from infrastructure.ml_tasks import process_document

        assert process_document.name == "ml.process_document"
        assert process_document.max_retries == 2

    def test_run_ocr_task_exists(self):
        from infrastructure.ml_tasks import run_ocr

        assert run_ocr.name == "ml.run_ocr"
        assert run_ocr.max_retries == 2

    def test_run_liveness_task_exists(self):
        from infrastructure.ml_tasks import run_liveness

        assert run_liveness.name == "ml.run_liveness"
        assert run_liveness.max_retries == 2

    def test_run_face_match_task_exists(self):
        from infrastructure.ml_tasks import run_face_match

        assert run_face_match.name == "ml.run_face_match"
        assert run_face_match.max_retries == 2

    def test_queue_assignments(self):
        from infrastructure.ml_tasks import (
            process_document,
            run_face_match,
            run_liveness,
            run_ocr,
        )

        assert process_document.queue == "cpu"
        assert run_ocr.queue == "cpu"
        assert run_liveness.queue == "gpu"
        assert run_face_match.queue == "gpu"

    def test_celery_queues_configured(self):
        from infrastructure.celery_app import celery_app

        queues = celery_app.conf.task_queues
        assert "realtime" in queues
        assert "gpu" in queues
        assert "cpu" in queues
        assert "async" in queues
