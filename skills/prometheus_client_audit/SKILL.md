---
name: prometheus_client_audit
description: Exposición de métricas FAR, FRR, tiempos de respuesta y tasas de fraude desde el audit_agent
type: Library
priority: Recomendada
mode: Self-hosted
---

# prometheus_client_audit

El audit_agent expone métricas Prometheus con las KPIs críticas del sistema KYC: tasa de aprobación/rechazo, FAR, FRR, tiempo medio del pipeline y detecciones de fraude. Estas métricas son consumidas por Grafana para los dashboards de negocio.

## When to use

Usar al persistir cada decisión de sesión. Incrementar los counters y actualizar los histogramas en el momento del commit a PostgreSQL.

## Instructions

1. Instalar: `pip install prometheus-client`
2. Definir métricas en `backend/metrics/kyc_metrics.py`:
   ```python
   from prometheus_client import Counter, Histogram, Gauge
   sessions_total = Counter("kyc_sessions_total", "Total sesiones procesadas", ["decision", "country"])
   pipeline_duration = Histogram("kyc_pipeline_duration_seconds", "Duración del pipeline completo", buckets=[1,2,4,6,8,10,15,30])
   fraud_detections = Counter("kyc_fraud_detections_total", "Fraudes detectados", ["fraud_type"])
   liveness_score = Histogram("kyc_liveness_score", "Distribución de scores de liveness", buckets=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
   face_match_score = Histogram("kyc_face_match_score", "Distribución de scores de face match", buckets=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])
   ```
3. Incrementar en `audit_agent.record_session()` tras cada decisión.
4. Exponer endpoint `/metrics` en cada servicio con `make_asgi_app()` de prometheus_client.
5. Configurar scraping en Prometheus: `scrape_interval: 15s`, target `audit_agent:8000/metrics`.
6. Crear alerta en Alertmanager si `far_rate > 0.001` (0.1%) o `frr_rate > 0.05` (5%) en ventana de 1 hora.

## Notes

- FAR = `approved_non_matching / total_attempted_fraud`. FRR = `rejected_matching / total_legitimate`.
- Los histogramas de score son útiles para detectar model drift: si la distribución cambia, alertar.
- Separar métricas de negocio (FAR/FRR) de métricas técnicas (latencia, CPU) — dashboards separados en Grafana.