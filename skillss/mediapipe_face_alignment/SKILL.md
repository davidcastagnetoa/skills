---
name: mediapipe_face_alignment
description: Alinear rostros por landmarks antes de generar embeddings — crítico para precisión de ArcFace
---

# mediapipe_face_alignment

La alineación facial normaliza la posición, escala y rotación del rostro antes de pasarlo al modelo de embeddings. Sin alinear, ArcFace puede perder hasta 15% de precisión en imágenes con cabeza inclinada o rostros en posición lateral.

## When to use

Aplicar siempre antes de extraer embeddings con InsightFace/ArcFace. Tanto para la selfie como para la foto del documento.

## Instructions

1. Instalar: `pip install mediapipe opencv-python-headless`
2. Implementar en `backend/agents/face_match/aligner.py`:
   ```python
   import mediapipe as mp
   import cv2, numpy as np
   face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)
   LEFT_EYE_IDX = 33   # landmark del ojo izquierdo
   RIGHT_EYE_IDX = 263  # landmark del ojo derecho
   def align_face(image: np.ndarray, output_size: tuple = (112, 112)) -> np.ndarray:
       results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
       if not results.multi_face_landmarks:
           raise ValueError("No face detected for alignment")
       landmarks = results.multi_face_landmarks[0].landmark
       h, w = image.shape[:2]
       left_eye = np.array([landmarks[LEFT_EYE_IDX].x * w, landmarks[LEFT_EYE_IDX].y * h])
       right_eye = np.array([landmarks[RIGHT_EYE_IDX].x * w, landmarks[RIGHT_EYE_IDX].y * h])
       angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))
       center = ((left_eye + right_eye) / 2).astype(int)
       M = cv2.getRotationMatrix2D(tuple(center), angle, 1.0)
       aligned = cv2.warpAffine(image, M, (w, h))
       # Crop y resize al tamaño esperado por ArcFace
       return cv2.resize(aligned[center[1]-56:center[1]+56, center[0]-56:center[0]+56], output_size)
   ```
3. El tamaño de salida debe ser `(112, 112)` — el input esperado por ArcFace R100.
4. Manejar la excepción cuando no se detecta cara: propagar como error de calidad al orchestrator.
5. Aplicar alineación tanto a la selfie como a la foto recortada del documento.

## Notes

- La alineación mejora la precisión más en casos difíciles: fotos de documento con inclinación, selfies sin centrar.
- Alternativa más rápida: usar los 5 puntos clave de InsightFace directamente en lugar de los 468 de MediaPipe.
- Procesar la alineación antes de la super-resolución (ESRGAN) para mejores resultados.