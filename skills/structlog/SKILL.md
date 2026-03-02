---
name: structlog
description: Logging JSON estructurado y de alto rendimiento con trazabilidad completa por sesión
---

# structlog

structlog es la librería de logging principal del sistema. Produce logs JSON estructurados que incluyen session_id, trace_id y todos los campos necesarios para correlacionar eventos a través del pipeline KYC.

## When to use

Usar en todos los agentes para emitir logs de cada evento significativo: inicio de sesión, resultado de cada agente, decisión final, errores y excepciones.

## Instructions

1. Instalar: `pip install structlog`
2. Configurar en `backend/core/logging.py`:
   ```python
   import structlog
   structlog.configure(
       processors=[
           structlog.contextvars.merge_contextvars,
           structlog.processors.add_log_level,
           structlog.processors.TimeStamper(fmt="iso"),
           structlog.processors.JSONRenderer(),
       ],
       wrapper_class=structlog.BoundLogger,
       logger_factory=structlog.PrintLoggerFactory(),
   )
   ```
3. Usar `structlog.contextvars.bind_contextvars(session_id=..., trace_id=...)` al inicio de cada request.
4. Obtener logger en cada módulo: `log = structlog.get_logger()`.
5. Emitir eventos con contexto: `log.info("liveness_result", score=0.87, decision="pass", agent="liveness_agent")`.
6. En caso de excepción: `log.exception("agent_error", agent="ocr_agent", error=str(e))`.
7. Integrar con OpenTelemetry via `structlog-contextvars` para propagar trace_id automáticamente.

## Notes

- Nunca loguear datos biométricos raw (embeddings, imágenes). Solo scores y decisiones.
- Nivel `DEBUG` solo en desarrollo; en producción usar `INFO` como mínimo.
- Los logs van a Grafana Loki via Promtail — el campo `session_id` es el índice de búsqueda primario.