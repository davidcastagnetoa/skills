---
name: temporal_compliance_validator
description: Verificar que el usuario completa cada challenge dentro del tiempo permitido
type: Algorithm
priority: Esencial
mode: Self-hosted
---

# temporal_compliance_validator

Valida que cada challenge activo se completa dentro de la ventana de tiempo permitida. Detecta ataques de replay lento y usuarios que intentan manipular la secuencia de frames.

## When to use

Usar como validador sobre cada challenge del liveness activo.

## Instructions

1. Al mostrar cada challenge al usuario, registrar `challenge_start_time = time.monotonic()`.
2. Definir tiempo máximo por challenge: `blink: 5s`, `head_turn: 4s`, `smile: 4s`.
3. Definir tiempo mínimo por challenge (muy rápido = sospechoso): `min_time: 0.5s`.
4. Si el usuario tarda más del máximo: `CHALLENGE_TIMEOUT` → reintentar o rechazar.
5. Si el usuario completa en menos del mínimo: `CHALLENGE_TOO_FAST` → posible ataque automatizado.
6. Verificar que los frames de cumplimiento del challenge son temporalmente consecutivos (sin gaps).
7. Emitir evento de auditoría con timestamps de inicio y fin de cada challenge.

## Notes

- Los tiempos máximos deben ser configurables para adaptarse a usuarios con discapacidades.
- Registrar el tiempo de respuesta en métricas para calibración de umbrales.