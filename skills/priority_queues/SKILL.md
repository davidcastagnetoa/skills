---
name: priority_queues
description: Colas separadas por prioridad con workers dedicados para garantizar SLO de latencia
type: Algorithm
priority: Esencial
mode: Self-hosted
---

# priority_queues

Colas de prioridad separadas garantizan que las tareas críticas de baja latencia (liveness) no compiten por workers con tareas menos urgentes (auditoría, análisis batch).

## When to use

Usar para segregar todas las tareas del pipeline KYC por nivel de urgencia.

## Instructions

1. Definir 4 colas en la configuración de Celery:
   - `realtime`: liveness, captura (SLO < 1s).
   - `gpu`: face_match, deepfake detection (SLO < 2s).
   - `cpu`: OCR, document processing (SLO < 3s).
   - `async`: auditoría, notificaciones, analytics (SLO < 30s).
2. Asignar tareas a colas con el decorador: `@app.task(queue='gpu')`.
3. Arrancar workers dedicados: `celery worker -Q realtime --concurrency=4 -P prefork`.
4. Asignar más workers a colas críticas.
5. Configurar `task_routes` en la configuración de Celery para enrutamiento automático.

## Notes

- Workers de cola GPU deben tener acceso a la GPU: `-P solo --concurrency=1` (un proceso por GPU).
- Monitorizar la profundidad de cada cola en Flower y Grafana.
