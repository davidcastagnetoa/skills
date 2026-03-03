---
name: prometheus_grafana
description: Stack de métricas y dashboards para visibilidad del pipeline KYC en tiempo real
type: Tool
priority: Esencial
mode: Self-hosted
---

# prometheus_grafana

Prometheus recolecta métricas de todos los servicios. Grafana las visualiza en dashboards. Juntos proporcionan visibilidad completa del rendimiento del pipeline y alertas tempranas.

## When to use

Instrumentar todos los agentes con métricas de Prometheus desde el primer día de desarrollo.

## Instructions

1. Instalar cliente Python: `pip install prometheus-client`.
2. Definir métricas en cada agente:
   ```python
   from prometheus_client import Counter, Histogram, Gauge
   verification_total = Counter('kyc_verifications_total', 'Total verifications', ['status'])
   pipeline_duration = Histogram('kyc_pipeline_duration_seconds', 'Pipeline latency', buckets=[0.5,1,2,4,8,16])
   active_sessions = Gauge('kyc_active_sessions', 'Active KYC sessions')
   ```
3. Exponer endpoint: `GET /metrics` en cada servicio.
4. Configurar Prometheus para scraping cada 15s.
5. Importar dashboards de Grafana para FastAPI, Celery, Redis, PostgreSQL, NVIDIA GPU desde Grafana Hub.
6. Crear dashboard KYC personalizado: tasa de aprobación/rechazo, latencia por fase, scores de distribución.
7. Configurar alertas: latencia p95 > 8s, tasa de error > 1%, GPU utilization < 10% (worker caído).

## Notes

- Helm chart: `kube-prometheus-stack` incluye Prometheus + Grafana + Alertmanager preconfigurado.
- Guardar los dashboards en Git como JSON para GitOps.