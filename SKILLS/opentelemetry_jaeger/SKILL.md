---
name: opentelemetry_jaeger
description: Trazabilidad distribuida del pipeline KYC para identificar cuellos de botella y depurar incidencias
---

# opentelemetry_jaeger

OpenTelemetry instrumenta el código para propagar `trace_id` y `span_id` a través de todos los agentes. Jaeger visualiza el flamegraph completo de cada sesión KYC.

## When to use

Instrumentar desde el inicio del desarrollo para poder depurar latencias y errores en producción.

## Instructions

1. Instalar: `pip install opentelemetry-sdk opentelemetry-exporter-jaeger opentelemetry-instrumentation-fastapi`.
2. Configurar tracer en el inicio de la aplicación:
   ```python
   from opentelemetry import trace
   from opentelemetry.exporter.jaeger.thrift import JaegerExporter
   from opentelemetry.sdk.trace import TracerProvider
   
   tracer_provider = TracerProvider()
   jaeger_exporter = JaegerExporter(agent_host_name="jaeger", agent_port=6831)
   tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
   trace.set_tracer_provider(tracer_provider)
   ```
3. Auto-instrumentar FastAPI: `FastAPIInstrumentor.instrument_app(app)`.
4. Crear spans manuales para cada agente: `with tracer.start_as_current_span("liveness_agent") as span: span.set_attribute("session_id", session_id)`.
5. Propagar contexto entre Celery tasks via baggage.
6. Visualizar en Jaeger UI: http://jaeger:16686.

## Notes

- Grafana Tempo es alternativa a Jaeger con mejor integración con Grafana Loki.
- Sampling: 100% en desarrollo, 10% en producción de alto tráfico.