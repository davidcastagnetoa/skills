"""Face embedding generation using ArcFace (InsightFace) with FaceNet fallback."""

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()

# ArcFace input specs
_ARCFACE_SIZE = (112, 112)
_EMBEDDING_DIM = 512


def preprocess_arcface(image: np.ndarray) -> np.ndarray:
    """Preprocess aligned face for ArcFace model.

    Args:
        image: BGR aligned face (112x112).

    Returns:
        Input tensor (1, 3, 112, 112) float32.
    """
    resized = cv2.resize(image, _ARCFACE_SIZE) if image.shape[:2] != _ARCFACE_SIZE else image
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = (rgb.astype(np.float32) - 127.5) / 127.5
    tensor = np.transpose(normalized, (2, 0, 1))  # HWC → CHW
    tensor = np.expand_dims(tensor, 0)
    return tensor


def generate_embedding(
    aligned_face: np.ndarray,
    session=None,  # onnxruntime.InferenceSession (ArcFace)
    session_backup=None,  # onnxruntime.InferenceSession (FaceNet backup)
) -> np.ndarray | None:
    """Generate a normalized face embedding vector.

    Uses ArcFace as primary model, FaceNet as fallback.

    Args:
        aligned_face: Aligned BGR face image (112x112).
        session: ArcFace ONNX session.
        session_backup: FaceNet ONNX session.

    Returns:
        Normalized embedding vector (512-d) or None if no model available.
    """
    # Try ArcFace
    if session is not None:
        embedding = _run_arcface(aligned_face, session)
        if embedding is not None:
            return embedding

    # Try FaceNet backup
    if session_backup is not None:
        embedding = _run_facenet(aligned_face, session_backup)
        if embedding is not None:
            return embedding

    logger.warning("embeddings.no_model_available")
    return None


def _run_arcface(image: np.ndarray, session) -> np.ndarray | None:
    """Run ArcFace inference."""
    tensor = preprocess_arcface(image)

    try:
        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: tensor})
        embedding = output[0][0].astype(np.float64)
        # L2 normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding
    except Exception:
        logger.exception("embeddings.arcface_failed")
        return None


def _run_facenet(image: np.ndarray, session) -> np.ndarray | None:
    """Run FaceNet inference (160x160 input)."""
    resized = cv2.resize(image, (160, 160))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = (rgb.astype(np.float32) - 127.5) / 128.0
    tensor = np.transpose(normalized, (2, 0, 1))
    tensor = np.expand_dims(tensor, 0)

    try:
        input_name = session.get_inputs()[0].name
        output = session.run(None, {input_name: tensor})
        embedding = output[0][0].astype(np.float64)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding
    except Exception:
        logger.exception("embeddings.facenet_failed")
        return None


def cosine_similarity(emb_a: np.ndarray, emb_b: np.ndarray) -> float:
    """Compute cosine similarity between two embedding vectors.

    Both vectors should be L2-normalized already, so the dot product
    equals cosine similarity.

    Returns:
        Similarity score in [-1, 1], typically [0, 1] for face embeddings.
    """
    if emb_a is None or emb_b is None:
        return 0.0

    similarity = float(np.dot(emb_a, emb_b))
    # Clamp to valid range
    return max(-1.0, min(1.0, similarity))
