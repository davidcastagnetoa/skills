#!/usr/bin/env bash
set -euo pipefail

MODELS_DIR="${1:-./models}"
echo "=== VerifID — Download ML Models ==="
echo "Target: ${MODELS_DIR}"

mkdir -p "${MODELS_DIR}"/{face_detection,face_recognition,face_alignment,anti_spoofing,depth_estimation,document_detection,ocr,deepfake}

download() {
    local url="$1"
    local dest="$2"
    if [ -f "$dest" ]; then
        echo "  [SKIP] $(basename "$dest") already exists"
        return
    fi
    echo "  [DOWN] $(basename "$dest")..."
    curl -fSL --progress-bar -o "$dest" "$url"
    echo "  [OK]   $(basename "$dest")"
}

# --- Face Detection: RetinaFace ---
echo ""
echo "[1/7] Face Detection (RetinaFace)..."
download \
    "https://huggingface.co/pfrancisco/insightface-onnx/resolve/main/det_10g.onnx" \
    "${MODELS_DIR}/face_detection/retinaface_r50.onnx"

# --- Face Recognition: ArcFace R50 ---
echo ""
echo "[2/7] Face Recognition (ArcFace)..."
download \
    "https://huggingface.co/pfrancisco/insightface-onnx/resolve/main/w600k_r50.onnx" \
    "${MODELS_DIR}/face_recognition/arcface_r100.onnx"

# --- Face Alignment: 2D-106 landmarks ---
echo ""
echo "[3/7] Face Alignment (2D-106)..."
download \
    "https://huggingface.co/pfrancisco/insightface-onnx/resolve/main/2d106det.onnx" \
    "${MODELS_DIR}/face_alignment/2d106det.onnx"

# --- Depth Estimation: MiDaS v2.1 small ---
echo ""
echo "[4/7] Depth Estimation (MiDaS)..."
download \
    "https://github.com/isl-org/MiDaS/releases/download/v2_1/midas_v21_small_256.onnx" \
    "${MODELS_DIR}/depth_estimation/midas_v21_small.onnx"

# --- Anti-Spoofing: Silent-Face ---
echo ""
echo "[5/7] Anti-Spoofing (Silent-Face)..."
echo "  [INFO] Silent-Face requires PyTorch→ONNX conversion. See docs/adr/ for details."
echo "  [INFO] Placeholder: run 'python scripts/convert_antispoof.py' after installing PyTorch."

# --- OCR: PaddleOCR ---
echo ""
echo "[6/7] OCR (PaddleOCR)..."
echo "  [INFO] PaddleOCR models are downloaded automatically by the paddleocr Python package."
echo "  [INFO] First inference will trigger download to ~/.paddleocr/"

# --- Deepfake Detection: XceptionNet ---
echo ""
echo "[7/7] Deepfake Detection (XceptionNet)..."
echo "  [INFO] XceptionNet weights require training on FaceForensics++ or downloading from a benchmark."
echo "  [INFO] Placeholder until model is available."

echo ""
echo "=== Download Complete ==="
echo "Models stored in: ${MODELS_DIR}"
echo ""
echo "Manual steps remaining:"
echo "  1. Convert Silent-Face PyTorch model to ONNX (scripts/convert_antispoof.py)"
echo "  2. Obtain XceptionNet weights for deepfake detection"
echo "  3. Verify checksums: python scripts/verify_checksums.py"
