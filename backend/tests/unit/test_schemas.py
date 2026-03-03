from core.schemas import VerificationRequest, VerificationResponse, VerificationStatus


def test_verification_request_valid() -> None:
    req = VerificationRequest(
        selfie_image="base64data",
        document_image="base64data",
        device_fingerprint="abc123",
    )
    assert req.selfie_image == "base64data"
    assert req.device_fingerprint == "abc123"
    assert req.metadata is None


def test_verification_request_minimal() -> None:
    req = VerificationRequest(
        selfie_image="data",
        document_image="data",
    )
    assert req.device_fingerprint is None


def test_verification_response_defaults() -> None:
    import uuid

    resp = VerificationResponse(
        session_id=uuid.uuid4(),
        status=VerificationStatus.PENDING,
    )
    assert resp.confidence_score is None
    assert resp.reasons == []
    assert resp.modules_scores is None


def test_verification_status_values() -> None:
    assert VerificationStatus.VERIFIED == "verified"
    assert VerificationStatus.REJECTED == "rejected"
    assert VerificationStatus.MANUAL_REVIEW == "manual_review"
