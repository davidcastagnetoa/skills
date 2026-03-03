---
name: mediapipe_face_mesh
description: 468 landmarks faciales precisos para detección de expresiones y orientación en liveness activo
type: ML Model
priority: Esencial
mode: Self-hosted
---

# mediapipe_face_mesh

MediaPipe Face Mesh genera 468 landmarks 3D en tiempo real. Es la base de todos los challenges activos: detección de parpadeo, giro de cabeza y expresiones faciales.

## When to use

Usar en todos los challenges de liveness activo que requieren detectar movimiento o expresión facial específica.

## Instructions

1. Instalar: `pip install mediapipe`.
2. Inicializar: `mp_face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)`.
3. Procesar frame: `results = mp_face_mesh.process(rgb_frame)`.
4. Extraer landmarks: `landmarks = results.multi_face_landmarks[0].landmark` → lista de 468 puntos (x, y, z normalizados).
5. Índices clave para cada tarea: ojos (33, 133, 159, 145, 158, 153 para ojo izquierdo), nariz (1, 4), boca (61, 291, 13, 14).
6. Proyectar coordenadas 3D a 2D con la dimensión del frame para cálculos de posición.

## Notes

- `refine_landmarks=True` añade landmarks de iris (precisión extra para blink detection).
- Ejecutar en hilo dedicado para no bloquear el pipeline principal.
- Documentación oficial: https://google.github.io/mediapipe/solutions/face_mesh