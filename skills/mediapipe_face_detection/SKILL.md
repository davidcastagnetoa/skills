---
name: mediapipe_face_detection
description: Verificar presencia de exactamente un rostro en la selfie antes de procesarla
type: ML Model
priority: Esencial
mode: Self-hosted
---

# mediapipe_face_detection

MediaPipe Face Detection detecta rostros en tiempo real con baja latencia (<10ms). Valida que el frame contiene exactamente un rostro con confianza suficiente.

## When to use

Ejecutar sobre cada frame capturado antes de enviarlo al liveness_agent.

## Instructions

1. `pip install mediapipe`
2. `mp_face = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.7)`
3. `results = mp_face.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))`
4. Verificar exactamente 1 detección: `if not results.detections or len(results.detections) != 1: reject()`
5. Cara debe ocupar al menos 15% del ancho del frame.
6. Cara centrada en ±25% del centro del frame.
7. Devolver bounding box para crop en pasos posteriores.

## Notes

- `model_selection=1` es largo alcance; `model_selection=0` es short-range (más rápido).
- Reutilizar la instancia del detector; no crear una nueva por frame.