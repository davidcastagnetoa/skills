---
name: realtime_user_feedback
description: Overlay en pantalla con instrucciones en tiempo real para guiar al usuario durante la captura
type: Framework
priority: Recomendada
mode: Self-hosted
---

# realtime_user_feedback

Sistema de feedback visual en tiempo real que guía al usuario durante la captura, reduciendo la tasa de capturas fallidas y mejorando la experiencia.

## When to use

Integrar en el frontend durante toda la sesión de captura, mostrando instrucciones contextuales.

## Instructions

1. Mapear cada condición de fallo a un mensaje claro:
   - `BLURRY` → "Mantén el teléfono más firme"
   - `OVEREXPOSED` → "Busca menos luz directa"
   - `NO_FACE` → "Centra tu cara en el óvalo"
   - `VIRTUAL_CAMERA` → "Usa la cámara real del dispositivo"
2. Mostrar feedback como overlay con animaciones suaves.
3. Para documento: overlay con rectángulo guía.
4. Indicador de progreso para challenges activos (tiempo restante).
5. Localizar mensajes en el idioma del usuario.

## Notes

- El feedback debe ser inmediato (<200ms de latencia percibida).
- Testear con usuarios reales; los mensajes técnicos confunden.