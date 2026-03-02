---
name: optical_flow_farneback
description: Detectar movimiento inconsistente o loop de video pregrabado mediante análisis de flujo óptico
---

# optical_flow_farneback

El flujo óptico de Farnebäck calcula el movimiento entre frames consecutivos. Los videos en loop o reproducidos tienen patrones de movimiento no naturales detectables con este análisis.

## When to use

Usar sobre la secuencia de frames del video de liveness para detectar ataques de replay y videos pregrabados.

## Instructions

1. Capturar mínimo 10 frames consecutivos del video de liveness.
2. Convertir a escala de grises.
3. Calcular flujo óptico entre pares de frames: `flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)`.
4. Calcular magnitud y ángulo del flujo: `magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])`.
5. Analizar estadísticas de magnitud: desviación estándar muy baja indica movimiento artificial.
6. Detectar loops: comparar el flujo acumulado entre frame 0 y frame N — si converge a 0, hay loop.
7. Analizar consistencia temporal: el movimiento natural tiene varianza creciente, no periódica.

## Notes

- Combinar con rPPG (Remote Photoplethysmography) para detección de vida aún más robusta.
- Sensible a iluminación variable; normalizar antes del análisis.