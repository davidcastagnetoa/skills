"""Age consistency checker.

Compares the estimated visual age of the selfie face with the
date of birth from the document to detect mismatches.
"""

from datetime import date

import cv2
import numpy as np
import structlog

from modules.antifraud.models import AgeConsistencyResult

logger = structlog.get_logger()

_AGE_TOLERANCE = 10  # Years of tolerance
_AGE_SUSPICIOUS_THRESHOLD = 15  # Flag if discrepancy > 15 years


def estimate_visual_age(
    face_image: np.ndarray,
    session=None,  # onnxruntime.InferenceSession (DEX or MiVOLO)
) -> int | None:
    """Estimate the visual age from a face image.

    Uses a deep age estimation model if available.
    Returns None if no model is loaded.
    """
    if session is None:
        return None

    try:
        # Preprocess for age estimation (224x224 input)
        resized = cv2.resize(face_image, (224, 224))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = rgb.astype(np.float32) / 255.0
        tensor = np.transpose(tensor, (2, 0, 1))
        tensor = np.expand_dims(tensor, 0)

        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: tensor})

        # Output is typically a softmax over age classes (0-100)
        probs = output[0][0]
        if len(probs) > 1:
            # Expected value (soft argmax)
            ages = np.arange(len(probs))
            estimated = float(np.sum(ages * probs))
        else:
            estimated = float(probs[0])

        return int(round(estimated))

    except Exception:
        logger.exception("age_estimation.inference_failed")
        return None


def calculate_age_from_dob(date_of_birth: str | None) -> int | None:
    """Calculate age from an ISO 8601 date of birth string."""
    if not date_of_birth:
        return None
    try:
        dob = date.fromisoformat(date_of_birth)
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except ValueError:
        return None


def check_age_consistency(
    face_image: np.ndarray | None,
    date_of_birth: str | None,
    age_model_session=None,
) -> AgeConsistencyResult:
    """Check consistency between visual age and document age.

    Args:
        face_image: BGR selfie face crop.
        date_of_birth: ISO 8601 date from document.
        age_model_session: ONNX session for age estimation.

    Returns:
        AgeConsistencyResult (non-blocking flag).
    """
    document_age = calculate_age_from_dob(date_of_birth)

    if face_image is None or document_age is None:
        return AgeConsistencyResult(document_age=document_age)

    estimated_age = estimate_visual_age(face_image, age_model_session)

    if estimated_age is None:
        return AgeConsistencyResult(document_age=document_age)

    discrepancy = abs(estimated_age - document_age)
    is_suspicious = discrepancy > _AGE_SUSPICIOUS_THRESHOLD

    if is_suspicious:
        logger.warning(
            "age_consistency.suspicious",
            estimated=estimated_age,
            document=document_age,
            discrepancy=discrepancy,
        )

    return AgeConsistencyResult(
        estimated_age=estimated_age,
        document_age=document_age,
        discrepancy_years=discrepancy,
        is_suspicious=is_suspicious,
    )
