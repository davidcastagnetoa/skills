---
name: timeout_manager
description: Gestión de timeouts por agente con cancelación limpia para cumplir el SLO de 8 segundos
---

# timeout_manager

Implementa timeouts individuales por agente y un timeout global de sesión, garantizando que el sistema siempre responde dentro del SLO de 8 segundos.

## When to use

Envolver cada llamada a un agente externo con un timeout configurado.

## Instructions

1. Instalar tenacity: `pip install tenacity`.
2. Para async: `await asyncio.wait_for(agent_coro(), timeout=AGENT_TIMEOUT_SECONDS)`.
3. Capturar `asyncio.TimeoutError` y registrar en auditoría.
4. Timeouts por agente: liveness=2s, ocr=2s, face_match=2s, antifraud=1s.
5. Si un agente no esencial supera el timeout, continuar con score de penalización.
6. Timeout global de sesión (8s) cancela todo y devuelve respuesta parcial con status TIMEOUT.

## Notes

- Usar `tenacity.retry` con `stop=stop_after_attempt(2)` para reintentos rápidos.
- Registrar histograma de latencia por agente en Prometheus.