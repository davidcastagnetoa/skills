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
