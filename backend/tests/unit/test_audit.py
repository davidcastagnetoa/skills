"""Tests for the audit module — anonymizer, hasher, and service."""

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.audit.anonymizer import (
    anonymize_data,
    mask_date,
    mask_document_number,
    mask_name,
)
from modules.audit.hasher import SessionHasher
from modules.audit.models import AuditEvent, AuditEventType, AuditTrail
from modules.audit.service import AuditService


# ── Anonymizer Tests ─────────────────────────────────────────────────

class TestMaskName:
    def test_simple_name(self):
        assert mask_name("Juan Garcia") == "J*** G***"

    def test_single_name(self):
        assert mask_name("Juan") == "J***"

    def test_empty(self):
        assert mask_name("") == ""

    def test_single_char(self):
        assert mask_name("J") == "J"

    def test_three_parts(self):
        assert mask_name("Juan Carlos Garcia") == "J*** C*** G***"


class TestMaskDocumentNumber:
    def test_standard_doc(self):
        result = mask_document_number("ABC12345678")
        assert "****" in result
        assert result.endswith("5678")

    def test_short_doc(self):
        result = mask_document_number("AB")
        assert result == "****"

    def test_empty(self):
        assert mask_document_number("") == "****"

    def test_none(self):
        assert mask_document_number(None) == "****"


class TestMaskDate:
    def test_standard_date(self):
        assert mask_date("1990-03-15") == "1990-**-**"

    def test_short_date(self):
        assert mask_date("1990") == "****-**-**"

    def test_empty(self):
        assert mask_date("") == "****-**-**"


class TestAnonymizeData:
    def test_name_fields(self):
        data = {"full_name": "Juan Garcia", "surname": "Garcia"}
        result = anonymize_data(data)
        assert result["full_name"] == "J*** G***"
        assert result["surname"] == "G***"

    def test_document_number(self):
        data = {"document_number": "ABC12345678"}
        result = anonymize_data(data)
        assert "****" in result["document_number"]

    def test_date_of_birth(self):
        data = {"date_of_birth": "1990-03-15"}
        result = anonymize_data(data)
        assert result["date_of_birth"] == "1990-**-**"

    def test_email(self):
        data = {"email": "user@example.com"}
        result = anonymize_data(data)
        assert "***" in result["email"]
        assert result["email"].startswith("u")

    def test_ip_address(self):
        data = {"ip_address": "192.168.1.100"}
        result = anonymize_data(data)
        assert result["ip_address"] == "192.168.1.***"

    def test_non_pii_passthrough(self):
        data = {"status": "verified", "score": 0.95}
        result = anonymize_data(data)
        assert result["status"] == "verified"
        assert result["score"] == 0.95

    def test_nested_dict(self):
        data = {"metadata": {"full_name": "Ana Lopez"}}
        result = anonymize_data(data)
        assert result["metadata"]["full_name"] == "A*** L***"


# ── Hasher Tests ─────────────────────────────────────────────────────

class TestSessionHasher:
    def setup_method(self):
        self.hasher = SessionHasher(b"test-secret-key")

    def test_hash_event_deterministic(self):
        event = {"session_id": "s1", "event_type": "session_created"}
        h1 = self.hasher.hash_event(event)
        h2 = self.hasher.hash_event(event)
        assert h1 == h2

    def test_hash_event_different_data(self):
        e1 = {"session_id": "s1"}
        e2 = {"session_id": "s2"}
        assert self.hasher.hash_event(e1) != self.hasher.hash_event(e2)

    def test_hash_trail_single_event(self):
        events = [{"session_id": "s1", "event_type": "created"}]
        h = self.hasher.hash_trail(events)
        assert len(h) == 64  # SHA-256 hex

    def test_hash_trail_chaining(self):
        events = [
            {"event": "first"},
            {"event": "second"},
        ]
        h_both = self.hasher.hash_trail(events)
        h_first = self.hasher.hash_trail([events[0]])
        assert h_both != h_first

    def test_hash_trail_order_matters(self):
        e1 = {"event": "first"}
        e2 = {"event": "second"}
        h_12 = self.hasher.hash_trail([e1, e2])
        h_21 = self.hasher.hash_trail([e2, e1])
        assert h_12 != h_21

    def test_verify_trail_valid(self):
        events = [{"event": "a"}, {"event": "b"}]
        expected = self.hasher.hash_trail(events)
        assert self.hasher.verify_trail(events, expected) is True

    def test_verify_trail_tampered(self):
        events = [{"event": "a"}, {"event": "b"}]
        assert self.hasher.verify_trail(events, "bad_hash") is False

    def test_different_keys_produce_different_hashes(self):
        hasher2 = SessionHasher(b"different-key")
        events = [{"event": "test"}]
        assert self.hasher.hash_trail(events) != hasher2.hash_trail(events)

    def test_empty_trail(self):
        h = self.hasher.hash_trail([])
        assert h == ""


# ── Models Tests ─────────────────────────────────────────────────────

class TestAuditModels:
    def test_event_type_values(self):
        assert AuditEventType.SESSION_CREATED.value == "session_created"
        assert AuditEventType.SESSION_COMPLETED.value == "session_completed"
        assert AuditEventType.DATA_PURGED.value == "data_purged"

    def test_audit_event_creation(self):
        event = AuditEvent(
            session_id="sess-1",
            event_type=AuditEventType.SESSION_CREATED,
            data={"key": "value"},
        )
        assert event.session_id == "sess-1"
        assert event.anonymized is False

    def test_audit_trail_creation(self):
        trail = AuditTrail(session_id="sess-1")
        assert trail.events == []
        assert trail.integrity_hash is None


# ── Service Tests ────────────────────────────────────────────────────

class TestAuditService:
    def setup_method(self):
        self.service = AuditService(db_session=None, secret_key=b"test-key")

    @pytest.mark.asyncio
    async def test_log_event_stores_in_memory(self):
        await self.service.log_event(
            "sess-1",
            AuditEventType.SESSION_CREATED,
            {"full_name": "Juan Garcia"},
        )
        assert "sess-1" in self.service._session_events
        assert len(self.service._session_events["sess-1"]) == 1

    @pytest.mark.asyncio
    async def test_log_event_anonymizes_pii(self):
        await self.service.log_event(
            "sess-1",
            AuditEventType.SESSION_CREATED,
            {"full_name": "Juan Garcia"},
        )
        stored = self.service._session_events["sess-1"][0]
        assert stored["data"]["full_name"] == "J*** G***"

    @pytest.mark.asyncio
    async def test_log_session_complete_returns_hash(self):
        await self.service.log_event(
            "sess-1", AuditEventType.SESSION_CREATED, {}
        )
        h = await self.service.log_session_complete("sess-1", "VERIFIED", 0.92)
        assert isinstance(h, str)
        assert len(h) == 64

    @pytest.mark.asyncio
    async def test_verify_trail_after_completion(self):
        await self.service.log_event(
            "sess-1", AuditEventType.SESSION_CREATED, {}
        )
        h = await self.service.log_session_complete("sess-1", "VERIFIED", 0.92)
        assert self.service.verify_trail("sess-1", h) is True

    @pytest.mark.asyncio
    async def test_verify_trail_detects_tampering(self):
        await self.service.log_event(
            "sess-1", AuditEventType.SESSION_CREATED, {}
        )
        await self.service.log_session_complete("sess-1", "VERIFIED", 0.92)
        assert self.service.verify_trail("sess-1", "tampered") is False

    @pytest.mark.asyncio
    async def test_log_error(self):
        await self.service.log_error("sess-1", ValueError("test error"))
        events = self.service._session_events["sess-1"]
        assert len(events) == 1
        assert events[0]["event_type"] == "session_error"
        assert events[0]["data"]["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_multiple_events_per_session(self):
        for etype in [
            AuditEventType.SESSION_CREATED,
            AuditEventType.CAPTURE_VALIDATED,
            AuditEventType.LIVENESS_COMPLETED,
        ]:
            await self.service.log_event("sess-1", etype, {})
        assert len(self.service._session_events["sess-1"]) == 3

    @pytest.mark.asyncio
    async def test_persist_skipped_without_db(self):
        # Should not raise even without db_session
        await self.service.log_event(
            "sess-1", AuditEventType.SESSION_CREATED, {}
        )
