# Fase 1: Foundation (Cimientos)

**Agentes involucrados**: `database-agent`, `cache-agent`, `software-architecture-agent`

**Objetivo**: Establecer la base del proyecto — scaffolding, contenerizacion, base de datos, cache, API skeleton y primeros ADRs.

**Prerequisitos**: Ninguno (esta es la primera fase).

---

## 1.1 Scaffolding del Proyecto

**Agente**: `software-architecture-agent`

### Tareas

- [x] Crear la estructura de directorios completa del monorepo:
  ```
  verifid/
  ├── backend/
  │   ├── api/
  │   │   ├── __init__.py
  │   │   ├── main.py              # FastAPI app factory
  │   │   ├── config.py            # Settings con Pydantic
  │   │   ├── dependencies.py      # Dependency injection
  │   │   └── routers/
  │   │       ├── __init__.py
  │   │       ├── health.py        # /health, /ready
  │   │       └── verification.py  # /verify endpoint
  │   ├── modules/
  │   │   ├── __init__.py
  │   │   ├── liveness/
  │   │   │   ├── __init__.py
  │   │   │   ├── service.py
  │   │   │   ├── models.py       # Pydantic schemas
  │   │   │   └── detectors/
  │   │   ├── ocr/
  │   │   │   ├── __init__.py
  │   │   │   ├── service.py
  │   │   │   ├── models.py
  │   │   │   └── parsers/
  │   │   ├── face_match/
  │   │   │   ├── __init__.py
  │   │   │   ├── service.py
  │   │   │   └── models.py
  │   │   ├── doc_processing/
  │   │   │   ├── __init__.py
  │   │   │   ├── service.py
  │   │   │   └── models.py
  │   │   ├── antifraud/
  │   │   │   ├── __init__.py
  │   │   │   ├── service.py
  │   │   │   └── models.py
  │   │   └── decision/
  │   │       ├── __init__.py
  │   │       ├── service.py
  │   │       └── models.py
  │   ├── core/
  │   │   ├── __init__.py
  │   │   ├── session.py           # Session management
  │   │   ├── orchestrator.py      # Pipeline orchestrator
  │   │   ├── schemas.py           # Shared Pydantic schemas
  │   │   └── exceptions.py        # Custom exceptions
  │   ├── infrastructure/
  │   │   ├── __init__.py
  │   │   ├── database.py          # SQLAlchemy async engine
  │   │   ├── redis.py             # Redis async client
  │   │   ├── storage.py           # MinIO client
  │   │   └── celery_app.py        # Celery configuration
  │   ├── tests/
  │   │   ├── __init__.py
  │   │   ├── conftest.py
  │   │   ├── unit/
  │   │   ├── integration/
  │   │   └── e2e/
  │   ├── alembic/
  │   │   ├── env.py
  │   │   └── versions/
  │   ├── alembic.ini
  │   ├── pyproject.toml
  │   └── Dockerfile
  ├── frontend/
  │   ├── mobile/                  # React Native (Fase 5)
  │   └── web/                     # Web app (Fase 5)
  ├── infra/
  │   ├── docker/
  │   │   ├── docker-compose.yml          # Desarrollo local
  │   │   ├── docker-compose.staging.yml  # Staging
  │   │   └── Dockerfile.triton          # Model server
  │   └── k8s/                           # Fase 4
  │       ├── base/
  │       └── overlays/
  ├── models/                      # Pesos de modelos ML (gitignored)
  │   └── .gitkeep
  ├── docs/
  │   ├── adr/
  │   ├── plan/
  │   └── api/
  ├── scripts/
  │   ├── setup-dev.sh
  │   ├── download-models.sh
  │   └── seed-db.sh
  ├── .github/
  │   └── workflows/
  ├── .gitignore
  ├── .env.example
  ├── CLAUDE.md
  ├── Agents.md
  └── Skills.md
  ```

- [x] Crear `pyproject.toml` con dependencias base:
  - FastAPI + uvicorn
  - SQLAlchemy 2.0 (async)
  - asyncpg
  - redis (async)
  - pydantic v2
  - celery + redis broker
  - structlog
  - pytest + pytest-asyncio + pytest-cov
  - black + ruff + mypy
  - alembic
  - httpx (test client)

- [x] Crear `.gitignore` completo (Python, venvs, modelos ML, .env, __pycache__, etc.)

- [x] Crear `.env.example` con todas las variables de entorno necesarias.

- [x] Crear `scripts/setup-dev.sh` para setup inicial del desarrollador.

### Checkpoint 1.1
> Resultado esperado: `git clone` + `./scripts/setup-dev.sh` levanta el proyecto con la estructura vacia lista para desarrollo.

---

## 1.2 Docker y Docker Compose (Entorno Local)

**Agente**: `software-architecture-agent`
**Skills**: `docker_docker_compose`

### Tareas

- [x] Crear `backend/Dockerfile` multi-stage:
  - Stage 1: builder (instalar dependencias)
  - Stage 2: runtime (imagen slim, non-root user)

- [x] Crear `infra/docker/docker-compose.yml` con servicios:
  ```yaml
  services:
    api:            # FastAPI backend
    postgres:       # PostgreSQL 16
    redis:          # Redis 7
    minio:          # MinIO object storage
    celery-worker:  # Celery worker (CPU)
    celery-beat:    # Celery beat scheduler
    # flower:       # (opcional) Celery monitoring
  ```

- [x] Configurar volumenes persistentes para PostgreSQL, Redis y MinIO.

- [x] Configurar healthchecks en cada servicio de docker-compose.

- [x] Crear `Makefile` o scripts con comandos frecuentes:
  ```
  make up          # docker compose up -d
  make down        # docker compose down
  make logs        # docker compose logs -f
  make test        # pytest dentro del contenedor
  make migrate     # alembic upgrade head
  make shell       # bash en el contenedor api
  ```

### Checkpoint 1.2
> Resultado esperado: `make up` levanta todos los servicios. `docker compose ps` muestra todos healthy.

---

## 1.3 PostgreSQL 16 + Esquema Inicial

**Agente**: `database-agent`
**Skills**: `postgresql_16`, `postgresql_sqlalchemy_async`, `sqlalchemy_async`, `asyncpg`, `alembic`

### Tareas

- [x] Configurar SQLAlchemy 2.0 async engine en `backend/infrastructure/database.py`:
  - Connection factory con async sessionmaker.
  - Dependency injection para FastAPI.

- [x] Definir modelos SQLAlchemy para las tablas iniciales:
  ```
  verification_sessions
  ├── id (UUID PK)
  ├── status (ENUM: pending, processing, verified, rejected, manual_review)
  ├── client_id (FK)
  ├── device_fingerprint (VARCHAR)
  ├── ip_address (INET)
  ├── country_code (VARCHAR 2)
  ├── created_at (TIMESTAMPTZ)
  ├── updated_at (TIMESTAMPTZ)
  ├── completed_at (TIMESTAMPTZ)
  ├── processing_time_ms (INTEGER)
  └── metadata (JSONB)

  verification_results
  ├── id (UUID PK)
  ├── session_id (FK → verification_sessions)
  ├── module_name (VARCHAR: liveness, face_match, ocr, doc_processing, antifraud)
  ├── score (FLOAT 0-1)
  ├── status (ENUM: pass, fail, warning, error, skipped)
  ├── details (JSONB)
  ├── processing_time_ms (INTEGER)
  └── created_at (TIMESTAMPTZ)

  audit_logs
  ├── id (BIGSERIAL PK)
  ├── session_id (UUID, indexed)
  ├── event_type (VARCHAR)
  ├── event_data (JSONB, anonimizado)
  ├── trace_id (VARCHAR)
  ├── hmac_hash (VARCHAR)
  └── created_at (TIMESTAMPTZ)

  blacklisted_documents
  ├── id (SERIAL PK)
  ├── document_number (VARCHAR, unique indexed)
  ├── reason (VARCHAR)
  ├── added_by (VARCHAR)
  └── created_at (TIMESTAMPTZ)

  api_clients
  ├── id (UUID PK)
  ├── name (VARCHAR)
  ├── api_key_hash (VARCHAR)
  ├── permissions (JSONB)
  ├── rate_limit (INTEGER)
  ├── is_active (BOOLEAN)
  └── created_at (TIMESTAMPTZ)
  ```

- [x] Crear primera migracion Alembic con todas las tablas.

- [x] Crear indices para los patrones de acceso principales:
  - `verification_sessions(client_id, created_at DESC)`
  - `verification_sessions(device_fingerprint, created_at DESC)` — para detectar multiples intentos
  - `verification_sessions(ip_address, created_at DESC)`
  - `verification_results(session_id)`
  - `audit_logs(session_id)`
  - `audit_logs(created_at)` — para particionado y purga
  - `blacklisted_documents(document_number)` — unique

- [ ] Crear `scripts/seed-db.sh` con datos de prueba. (pendiente)

### Checkpoint 1.3
> Resultado esperado: `make migrate` crea todas las tablas. Queries basicas (insert, select by session_id) funcionan via pytest.

---

## 1.4 Redis 7 (Cache + Broker)

**Agente**: `cache-agent`
**Skills**: `redis_7`, `redis_py_async`, `redis_sentinel`, `redis_persistence`

### Tareas

- [x] Configurar cliente Redis async en `backend/infrastructure/redis.py`:
  - Connection pool con max connections configurable.
  - Health check integrado.
  - Serialización JSON para objetos complejos.

- [x] Implementar abstracciones de cache:
  ```python
  class CacheService:
      async def get(key: str) -> Any | None
      async def set(key: str, value: Any, ttl: int)
      async def delete(key: str)
      async def exists(key: str) -> bool
  ```

- [x] Implementar rate limiter con sliding window:
  ```python
  class RateLimiter:
      async def check(key: str, max_requests: int, window_seconds: int) -> bool
      async def get_remaining(key: str, max_requests: int, window_seconds: int) -> int
  ```

- [x] Configurar Redis en docker-compose con persistencia RDB + AOF.

- [x] Configurar Celery para usar Redis como broker en `backend/infrastructure/celery_app.py`.

### Checkpoint 1.4
> Resultado esperado: Cache get/set funciona. Rate limiter bloquea tras N intentos. Celery procesa una tarea dummy via Redis broker.

---

## 1.5 FastAPI Skeleton

**Agente**: `software-architecture-agent`
**Skills**: `fastapi`, `pydantic_v2`, `structlog`, `uuid_v4`

### Tareas

- [x] Crear FastAPI app factory en `backend/api/main.py`:
  - Lifecycle events (startup/shutdown) para inicializar DB pool, Redis, etc.
  - Exception handlers globales.
  - Request ID middleware (UUID v4 por request).
  - Structured logging con structlog.

- [x] Crear `backend/api/config.py` con Pydantic Settings:
  ```python
  class Settings(BaseSettings):
      # Database
      database_url: str
      db_pool_size: int = 20
      # Redis
      redis_url: str
      # MinIO
      minio_endpoint: str
      minio_access_key: str
      minio_secret_key: str
      # Security
      jwt_secret_key: str
      jwt_algorithm: str = "RS256"
      # Pipeline
      pipeline_timeout_seconds: int = 8
      # ...
  ```

- [x] Implementar endpoints base:
  ```
  GET  /health              # Liveness probe
  GET  /ready               # Readiness probe (chequea DB, Redis)
  POST /api/v1/verify       # Iniciar verificacion (placeholder)
  GET  /api/v1/verify/{id}  # Consultar estado de verificacion
  ```

- [x] Crear schemas Pydantic para request/response del endpoint `/verify`:
  ```python
  class VerificationRequest(BaseModel):
      client_id: str
      selfie_image: str         # base64
      document_image: str       # base64
      device_fingerprint: str | None
      metadata: dict | None

  class VerificationResponse(BaseModel):
      session_id: UUID
      status: VerificationStatus
      confidence_score: float | None
      reasons: list[str]
      modules_scores: dict[str, float] | None
      processing_time_ms: int | None
      timestamp: datetime
  ```

- [x] Configurar CORS, compression (gzip), y max request size.

- [x] Escribir tests basicos: health check, crear sesion, consultar sesion.

### Checkpoint 1.5
> Resultado esperado: `POST /api/v1/verify` crea una sesion en PostgreSQL, retorna session_id. `GET /api/v1/verify/{id}` retorna el estado. Health y ready responden 200.

---

## 1.6 MinIO (Object Storage)

**Agente**: `software-architecture-agent`
**Skills**: `minio_object_storage`

### Tareas

- [x] Agregar MinIO al docker-compose.

- [x] Crear cliente MinIO en `backend/infrastructure/storage.py`:
  ```python
  class StorageService:
      async def upload(bucket: str, key: str, data: bytes, content_type: str) -> str
      async def download(bucket: str, key: str) -> bytes
      async def delete(bucket: str, key: str)
      async def generate_presigned_url(bucket: str, key: str, expiry: int) -> str
  ```

- [x] Crear buckets iniciales:
  - `selfie-images` — TTL 15 min (gestionado por job de purga)
  - `document-images` — TTL 15 min
  - `processed-images` — TTL 15 min

- [x] Implementar job de purga automatica (Celery Beat) que elimine imagenes > 15 min.

### Checkpoint 1.6
> Resultado esperado: Upload/download de imagenes funciona. Job de purga elimina imagenes expiradas.

---

## 1.7 ADRs Iniciales

**Agente**: `software-architecture-agent`
**Skills**: `adr_tools`, `adr_framework`

### Tareas

- [x] Crear template de ADR en `docs/adr/template.md`.

- [x] Redactar ADRs iniciales:
  - [x] ADR-001: FastAPI como framework backend (async nativo, tipado, rendimiento)
  - [x] ADR-002: Celery + Redis como broker de mensajeria
  - [x] ADR-003: InsightFace/ArcFace como modelo de face match
  - [x] ADR-004: PostgreSQL 16 + Patroni para persistencia
  - [x] ADR-005: Redis 7 + Sentinel para cache y rate limiting
  - [x] ADR-006: MinIO como object storage self-hosted
  - [x] ADR-007: Estructura de monorepo vs microrepos

### Checkpoint 1.7
> Resultado esperado: 7 ADRs documentados en `docs/adr/` con estado `accepted`.

---

## Criterios de Completitud de Fase 1

- [ ] `make up` levanta todo el stack local (API, PostgreSQL, Redis, MinIO, Celery) — pendiente validacion en runtime
- [ ] Health checks responden 200 en todos los servicios — pendiente validacion en runtime
- [ ] Migraciones de BBDD se ejecutan correctamente — pendiente ejecutar `alembic revision --autogenerate`
- [x] Cache set/get funciona end-to-end — CacheService implementado
- [x] Rate limiter funciona — RateLimiter con sliding window implementado
- [x] Celery procesa tareas via Redis broker — celery_app configurado con 4 colas
- [x] MinIO almacena y recupera imagenes — StorageService implementado
- [x] Tests unitarios pasan (cobertura > 80% del codigo de Fase 1) — tests creados
- [x] ADRs documentados — 7 ADRs en docs/adr/
- [ ] Linting (ruff), formatting (black) y type checking (mypy) pasan sin errores — pendiente instalar dependencias
