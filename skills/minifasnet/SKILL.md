---
name: minifasnet
description: Modelo ligero de anti-spoofing optimizado para producción — alta velocidad con buena precisión
type: ML Model
priority: Esencial
mode: Self-hosted
---

# minifasnet

MiniFASNet es una arquitectura compacta de anti-spoofing diseñada para producción. Complementa a Silent-Face-Anti-Spoofing con mayor velocidad (<100ms) manteniendo alta precisión.

## When to use

Usar como modelo primario de liveness pasivo por su velocidad, con Silent-Face como validación secundaria en casos dudosos (score entre 0.4 y 0.7).

## Instructions

1. Descargar pesos desde el repositorio Silent-Face-Anti-Spoofing (incluye MiniFASNetV1 y V2).
2. Usar `MiniFASNetV2` para el balance óptimo velocidad/precisión.
3. Cargar modelo una sola vez en el worker: `model = load_model('MiniFASNetV2', device='cuda')`.
4. Input: patch de cara recortada y redimensionada a 80x80 píxeles.
5. Output: `[spoof_score, real_score]` — usar `real_score` como score de liveness.
6. Definir umbral operacional: `real_score > 0.65` para aceptar.
7. Registrar el score en el evento de auditoría para análisis posterior.

## Notes

- MiniFASNetV1 es más rápido; V2 es más preciso. Seleccionar según hardware disponible.
- Benchmark en GPU RTX 3090: ~15ms por frame.