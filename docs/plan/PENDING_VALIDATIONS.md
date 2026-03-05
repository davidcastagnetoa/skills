# Validaciones Pendientes de Runtime

Estas validaciones requieren Docker corriendo y deben ejecutarse antes de considerar la fase completada al 100%.

## Fase 1 — Foundation

- [ ] Ejecutar `make up` y verificar que todos los servicios suben (PostgreSQL, Redis, MinIO, API, Celery worker, Celery beat)
- [ ] Generar primera migracion de Alembic: `cd backend && alembic revision --autogenerate -m "initial schema"`
- [ ] Ejecutar migracion: `make migrate`
- [ ] Verificar que `GET /health` responde 200
- [ ] Verificar que `GET /ready` responde 200 con todos los checks en true
- [ ] Ejecutar `POST /api/v1/verify` con datos dummy y verificar que crea sesion en PostgreSQL
- [ ] Ejecutar `make test` y verificar que todos los tests pasan
- [ ] Ejecutar `make lint` y `make typecheck` — corregir errores si los hay
- [ ] Crear `scripts/seed-db.sh` con datos de prueba (blacklisted documents, api client)
- [ ] Verificar que MinIO tiene los 3 buckets creados (selfie-images, document-images, processed-images)

## Fase 2 — Core ML Pipeline

- [ ] Ejecutar todos los tests: `python -m pytest tests/unit/ -v`
  - `test_doc_processing.py` — 27 tests
  - `test_ocr.py` — 26 tests
  - `test_liveness.py` — 25 tests
  - `test_face_match.py` — 24 tests
  - `test_ml_tasks.py` — 6 tests
- [ ] Verificar carga de modelos ONNX con `scripts/download-models.sh`
- [ ] Medir tiempos de inferencia por módulo (doc_processing < 2s, OCR < 2s, liveness < 2s, face_match < 500ms)
- [ ] Ejecutar Celery worker con `celery -A infrastructure.celery_app worker -Q cpu,gpu` y enviar tarea de prueba
- [ ] Validar FAR/FRR con dataset de test (mínimo 100 pares positivos/negativos)
- [ ] Validar tasa de detección de spoofing con imágenes de ataque

## Fase 3 — Pipeline Integration

- [ ] Ejecutar tests de Phase 3: `python -m pytest tests/unit/test_capture.py tests/unit/test_antifraud.py tests/unit/test_decision.py tests/unit/test_audit.py tests/unit/test_orchestrator.py -v`
- [ ] Ejecutar pipeline end-to-end con `POST /api/v1/verify` (selfie + documento reales)
- [ ] Verificar que `GET /api/v1/verify/{id}` retorna progreso y resultado final
- [ ] Verificar timeout de 8 segundos funciona (con módulo lento simulado)
- [ ] Verificar degradación graceful: liveness falla → MANUAL_REVIEW, OCR falla → penalización, doc_processing falla → REJECTED
- [ ] Verificar que los 10 escenarios de fraude del CLAUDE.md se detectan correctamente
- [ ] Verificar que audit trail se genera completo con PII anonimizado y hash de integridad
- [ ] Verificar pesos del decision engine configurables via Redis sin redeploy
- [ ] Verificar cola de revisión manual para sesiones ambiguas
- [ ] Medir rendimiento end-to-end: pipeline completo < 8 segundos

## Fase 4 — Production Infrastructure

- [ ] Verificar que Nginx proxea correctamente a FastAPI con TLS
- [ ] Verificar JWT validation y API key auth en Nginx Lua
- [ ] Verificar rate limiting (60 req/min general, 10 req/min /verify)
- [ ] Verificar circuit breaker Lua ante fallos del upstream
- [ ] Verificar dashboards Grafana cargan datos reales de Prometheus
- [ ] Verificar trazas en Jaeger con trace_id correlacionado en logs
- [ ] Verificar health checks `/health` y `/ready` con dependencias caidas
- [ ] Verificar circuit breakers Python (PostgreSQL, Redis, MinIO, model_server)
- [ ] Verificar Alertmanager recibe alertas de Prometheus
- [ ] Verificar Vault integration (secretos inyectados al arrancar)
- [ ] Verificar cifrado/descifrado AES-256-GCM en MinIO
- [ ] Verificar RBAC (admin/operator/reviewer/client permissions)
- [ ] Verificar PostgreSQL HA: `docker compose -f docker-compose.yml -f docker-compose.ha.yml up`
- [ ] Verificar PgBouncer connection pooling (max 200 clients, pool size 20)
- [ ] Verificar pgBackRest full + diff backup a MinIO
- [ ] Verificar Triton Inference Server con modelos ONNX cargados
- [ ] Verificar fallback de Triton a ONNX Runtime local
- [ ] Verificar CI pipeline: `gh workflow run ci.yml`
- [ ] Verificar pre-commit hooks: `pre-commit run --all-files`
- [ ] Verificar Helm chart: `helm template verifid infra/k8s/ -f infra/k8s/values.yaml`
- [ ] Verificar HPA escala pods bajo carga con k6/locust
