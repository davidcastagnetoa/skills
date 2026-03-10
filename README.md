# VerifID — Sistema de Verificacion de Identidad (KYC)

Sistema de verificacion de identidad que compara un documento (DNI, pasaporte) con una selfie en vivo para confirmar la identidad del usuario.

## Stack Tecnologico

| Capa                  | Tecnologia                                     |
| --------------------- | ---------------------------------------------- |
| Backend               | Python (FastAPI)                               |
| Mobile                | React Native (Expo ~52)                        |
| Web                   | React + Vite + WebRTC                          |
| Reconocimiento facial | InsightFace (ArcFace) — self-hosted            |
| Liveness Detection    | Silent-Face-Anti-Spoofing + Challenge-Response |
| OCR                   | PaddleOCR / EasyOCR — self-hosted              |
| Base de datos         | PostgreSQL + Redis                             |
| Infraestructura       | Docker + Kubernetes                            |

## Estructura del Proyecto

```
verifid/
├── backend/          # API FastAPI + modulos ML
├── frontend/
│   ├── mobile/       # React Native (Expo)
│   └── web/          # React + Vite + WebRTC
├── infra/            # Docker + Kubernetes
└── docs/plan/        # Documentacion de fases
```

---

## Frontend Mobile (frontend/mobile/)

App React Native con Expo para iOS y Android.

### Pantallas

| Pantalla          | Archivo                            | Descripcion                                       |
| ----------------- | ---------------------------------- | ------------------------------------------------- |
| Welcome           | `app/screens/WelcomeScreen.tsx`    | Explica el proceso, solicita permiso de camara    |
| Selfie Capture    | `app/screens/SelfieCapture.tsx`    | Captura selfie con camara frontal y ovalo guia    |
| Active Challenges | `app/screens/ActiveChallenges.tsx` | Desafios liveness: parpadeo, giro, sonrisa        |
| Document Capture  | `app/screens/DocumentCapture.tsx`  | Captura documento con camara trasera y marco guia |
| Processing        | `app/screens/ProcessingScreen.tsx` | Envia al backend, muestra progreso por fase       |
| Result            | `app/screens/ResultScreen.tsx`     | Muestra resultado (verificado/rechazado/revision) |
| Error             | `app/screens/ErrorScreen.tsx`      | Pantalla de error con opcion de reintento         |

### Componentes

| Componente          | Proposito                                       |
| ------------------- | ----------------------------------------------- |
| `FaceOval`          | Ovalo guia para alinear el rostro en selfie     |
| `FeedbackMessage`   | Pill flotante con feedback en tiempo real       |
| `ChallengePrompt`   | Instrucciones visuales para cada desafio        |
| `DocumentGuide`     | Marco con esquinas para alinear documento       |
| `ProgressIndicator` | Lista de fases con checkmarks                   |
| `CameraOverlay`     | Contenedor transparente para overlays de camara |

### Hooks

| Hook               | Proposito                                                 |
| ------------------ | --------------------------------------------------------- |
| `useCamera`        | Captura de frames y fotos con expo-camera                 |
| `useFaceDetection` | Deteccion de rostro on-device (stub, pendiente MediaPipe) |
| `useVerification`  | Estado y flujo de verificacion completo                   |
| `useDeviceInfo`    | Info del dispositivo + fingerprint SHA256                 |

### Servicios

| Servicio               | Proposito                                                               |
| ---------------------- | ----------------------------------------------------------------------- |
| `api.ts`               | Cliente HTTP (Axios) con `startVerification`, `getStatus`, `pollResult` |
| `deviceFingerprint.ts` | Recopila info del dispositivo y genera hash SHA256                      |

### Configuracion Expo

- Permisos: `CAMERA` (Android), `NSCameraUsageDescription` (iOS)
- Plugins: `expo-camera`
- Bundle ID: `com.advantra.verifid`

### Comandos

```bash
cd frontend/mobile
npm install
npm start          # Expo dev server
npm run ios        # iOS simulator
npm run android    # Android emulator
npm run typecheck  # TypeScript check
```

---

## Frontend Web (frontend/web/)

App React con Vite y WebRTC para navegadores.

### Paginas

| Pagina              | Ruta          | Descripcion                                   |
| ------------------- | ------------- | --------------------------------------------- |
| WelcomePage         | `/`           | Inicio y explicacion del proceso              |
| SelfieCapturePage   | `/selfie`     | Captura selfie via WebRTC (camara frontal)    |
| ChallengesPage      | `/challenges` | Desafios liveness                             |
| DocumentCapturePage | `/document`   | Captura documento via WebRTC (camara trasera) |
| ProcessingPage      | `/processing` | Envio al backend y polling de resultado       |
| ResultPage          | `/result`     | Resultado de la verificacion                  |

### Hook: useWebRTCCamera

Acceso a camara via `navigator.mediaDevices.getUserMedia`. Soporta:

- Seleccion de camara (frontal/trasera via `facingMode`)
- Captura de frame unico o secuencia de frames
- Captura de alta calidad para documentos

### Comandos

```bash
cd frontend/web
npm install
npm run dev        # Vite dev server (puerto 3000)
npm run build      # Build produccion
npm run typecheck  # TypeScript check
```

### Proxy

El Vite dev server proxea `/api` a `http://localhost:8000` (backend FastAPI).

---

## Backend (backend/)

API FastAPI con modulos de procesamiento ML. Python 3.12+, dependencias gestionadas con `pyproject.toml`.

### Modulos

| Modulo            | Responsabilidad                                        |
| ----------------- | ------------------------------------------------------ |
| `liveness/`       | Deteccion de vida (passive + active + challenge)       |
| `ocr/`            | Extraccion de texto, MRZ y validacion ICAO 9303        |
| `face_match/`     | Comparacion biometrica facial (ArcFace embeddings)     |
| `doc_processing/` | Deteccion de bordes, perspectiva, mejora, anti-forgery |
| `antifraud/`      | Blacklist, geoIP, multi-attempt, age consistency       |
| `decision/`       | Motor de decision ponderado con reglas configurables   |
| `capture/`        | Validacion de calidad, virtual camera, gallery blocker |
| `audit/`          | Logging inmutable, PII anonymizer, hash integridad     |
| `orchestrator/`   | Director del pipeline con timeout y degradacion        |

### Endpoints principales

| Metodo | Ruta                                       | Descripcion                                      |
| ------ | ------------------------------------------ | ------------------------------------------------ |
| POST   | `/api/v1/verification/start`               | Inicia verificacion con selfie + documento       |
| GET    | `/api/v1/verification/{session_id}/status` | Consulta estado/resultado de una sesion          |
| GET    | `/health`                                  | Health check basico (liveness probe)             |
| GET    | `/ready`                                   | Readiness check con estado de dependencias       |

### Infraestructura del backend

| Componente          | Archivo                          | Descripcion                                  |
| ------------------- | -------------------------------- | -------------------------------------------- |
| Config              | `api/config.py`                  | Settings con Pydantic (desde env vars)       |
| Database            | `infrastructure/database.py`     | SQLAlchemy async + connection pool           |
| Models              | `infrastructure/models.py`       | Modelos SQLAlchemy (sessions, audit, etc.)   |
| Redis               | `infrastructure/redis.py`        | Cliente Redis async                          |
| Celery              | `infrastructure/celery_app.py`   | App Celery con colas cpu/async               |
| ML Tasks            | `infrastructure/ml_tasks.py`     | Tareas Celery para inferencia ML             |
| Storage             | `infrastructure/storage.py`      | Cliente MinIO para imagenes temporales       |
| Schemas             | `core/schemas.py`                | Schemas Pydantic de request/response         |
| Orchestrator        | `core/orchestrator.py`           | Orquestador del pipeline de verificacion     |
| Alembic migrations  | `alembic/`                       | Migraciones de base de datos                 |

### Comandos backend (via Makefile)

```bash
# --- Setup inicial ---
bash scripts/setup-dev.sh          # Setup completo automatizado (venv + deps + docker + migrations)

# --- Docker (infraestructura) ---
make up                            # Levantar todos los servicios (PostgreSQL, Redis, MinIO, API, Celery, Prometheus, Grafana, Jaeger)
make down                          # Parar servicios
make down-volumes                  # Parar y borrar volumenes
make logs                          # Ver logs de todos los servicios
make ps                            # Estado de los contenedores
make rebuild                       # Rebuild y restart

# --- Base de datos ---
make migrate                       # Ejecutar migraciones pendientes
make migrate-create msg="nombre"   # Crear nueva migracion
make migrate-downgrade             # Revertir ultima migracion

# --- Tests ---
make test                          # Todos los tests
make test-unit                     # Solo tests unitarios
make test-integration              # Solo tests de integracion
make test-cov                      # Tests con cobertura (umbral 80%)

# --- Calidad de codigo ---
make lint                          # Ruff linter
make format                        # Ruff formatter
make typecheck                     # Mypy type checking
make quality                       # lint + typecheck

# --- Acceso interactivo ---
make shell                         # Bash dentro del contenedor API
make psql                          # Consola PostgreSQL
make redis-cli                     # Consola Redis

# --- Limpieza ---
make clean                         # Borrar __pycache__, .pytest_cache, etc.
```

### Setup manual del backend (sin Docker)

```bash
# 1. Crear virtualenv
python3 -m venv backend/.venv
source backend/.venv/bin/activate

# 2. Instalar dependencias
pip install -e "backend[dev]"       # Core + dev tools
pip install -e "backend[ml]"       # + dependencias ML (opencv, onnx, mediapipe, etc.)

# 3. Copiar variables de entorno
cp .env.example .env               # Editar con valores reales si es necesario

# 4. Levantar dependencias con Docker
make up

# 5. Ejecutar migraciones
make migrate

# 6. Ejecutar la API en modo desarrollo
cd backend && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 7. Ejecutar Celery worker (en otro terminal)
cd backend && celery -A infrastructure.celery_app worker --loglevel=info -Q cpu,async
```

---

## Pruebas en Local

### Prerequisitos

- Python 3.12+
- Docker y Docker Compose
- Node.js 18+ (para frontend)

### 1. Levantar todo el sistema

```bash
# Setup automatico (primera vez)
bash scripts/setup-dev.sh

# O manualmente:
cp .env.example .env
make up                            # Levanta PostgreSQL, Redis, MinIO, API, Celery, Prometheus, Grafana, Jaeger
make migrate                       # Crea las tablas
```

### 2. Verificar que los servicios estan corriendo

```bash
make ps                            # Ver estado de contenedores

# Health checks
curl http://localhost:8000/health   # Debe retornar 200
curl http://localhost:8000/ready    # Debe retornar 200 con checks en true
```

### 3. Acceder a las interfaces web

| Servicio     | URL                        | Credenciales         |
| ------------ | -------------------------- | -------------------- |
| API Docs     | http://localhost:8000/docs | -                    |
| MinIO        | http://localhost:9001      | minioadmin/minioadmin |
| Grafana      | http://localhost:3000      | admin/verifid        |
| Prometheus   | http://localhost:9090      | -                    |
| Jaeger       | http://localhost:16686     | -                    |
| Alertmanager | http://localhost:9093      | -                    |

### 4. Ejecutar tests del backend

```bash
make test                          # Todos los tests
make test-unit                     # Solo unitarios (rapido, sin dependencias externas)
make test-cov                      # Con reporte de cobertura

# Tests especificos por modulo
cd backend
.venv/bin/pytest tests/unit/test_doc_processing.py -v    # 27 tests
.venv/bin/pytest tests/unit/test_ocr.py -v               # 26 tests
.venv/bin/pytest tests/unit/test_liveness.py -v           # 25 tests
.venv/bin/pytest tests/unit/test_face_match.py -v         # 24 tests
.venv/bin/pytest tests/unit/test_ml_tasks.py -v           # 6 tests
.venv/bin/pytest tests/unit/test_capture.py -v
.venv/bin/pytest tests/unit/test_antifraud.py -v
.venv/bin/pytest tests/unit/test_decision.py -v
.venv/bin/pytest tests/unit/test_audit.py -v
.venv/bin/pytest tests/unit/test_orchestrator.py -v
```

### 5. Probar el flujo de verificacion manualmente

```bash
# Iniciar una verificacion (reemplazar con datos base64 reales)
curl -X POST http://localhost:8000/api/v1/verification/start \
  -H "Content-Type: application/json" \
  -d '{
    "selfie_frames": ["base64_frame_1", "base64_frame_2"],
    "document_image": "base64_document",
    "device_fingerprint": "abc123",
    "challenges": [{"type": "blink", "passed": true, "timestamp_ms": 1700000000}]
  }'

# Consultar estado (reemplazar SESSION_ID)
curl http://localhost:8000/api/v1/verification/SESSION_ID/status
```

### 6. Probar el frontend web contra el backend

```bash
# Terminal 1: Backend
make up

# Terminal 2: Frontend web
cd frontend/web && npm install && npm run dev
# Abrir http://localhost:3000 — el proxy de Vite redirige /api a :8000
```

### 7. Probar el frontend mobile

```bash
# Terminal 1: Backend (asegurar que esta corriendo)
make up

# Terminal 2: Expo
cd frontend/mobile && npm install && npm start
# Escanear QR con Expo Go, o pulsar 'i' para iOS simulator / 'a' para Android emulator
# La app apunta a EXPO_PUBLIC_API_URL (default: http://localhost:8000)
```

---

## Variables de Entorno

Copiar `.env.example` a `.env`. Variables principales:

| Variable                  | Descripcion                                        | Default                |
| ------------------------- | -------------------------------------------------- | ---------------------- |
| `APP_ENV`                 | Entorno (development/staging/production)            | `development`          |
| `DATABASE_URL`            | Connection string PostgreSQL (asyncpg)              | `postgresql+asyncpg://verifid:verifid_secret@localhost:5432/verifid` |
| `REDIS_URL`               | URL de Redis                                       | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL`       | Broker para Celery                                 | `redis://localhost:6379/1` |
| `MINIO_ENDPOINT`          | Endpoint MinIO                                     | `localhost:9000`       |
| `MINIO_ACCESS_KEY`        | Access key MinIO                                   | `minioadmin`           |
| `MINIO_SECRET_KEY`        | Secret key MinIO                                   | `minioadmin`           |
| `MINIO_IMAGE_TTL_MINUTES` | TTL de imagenes temporales                         | `15`                   |
| `JWT_SECRET_KEY`          | Clave secreta para JWT (cambiar en produccion)     | -                      |
| `ENCRYPTION_KEY`          | Clave AES-256 para cifrado biometrico              | -                      |
| `FACE_MATCH_THRESHOLD`    | Umbral de similitud facial (0-1)                   | `0.85`                 |
| `LIVENESS_THRESHOLD`      | Umbral de deteccion de vida (0-1)                  | `0.7`                  |
| `PIPELINE_TIMEOUT_SECONDS`| Timeout maximo del pipeline                        | `8`                    |
| `CORS_ORIGINS`            | Origenes permitidos                                | `http://localhost:3000,http://localhost:8081` |
| `AUTH_BYPASS`             | Saltear autenticacion (solo desarrollo)            | `true`                 |
| `EXPO_PUBLIC_API_URL`     | URL del backend para la app mobile                 | `http://localhost:8000` |
| `VITE_API_URL`            | URL del backend para la web                        | (usa proxy en dev)     |

Ver `.env.example` para la lista completa.

---

## Modelos ML

```bash
# Descargar modelos pre-entrenados (ArcFace, anti-spoof, MiDaS, etc.)
bash scripts/download-models.sh

# Los modelos se guardan en /models y se montan como volumen read-only en Docker
```

---

## Estado de Implementacion

| Fase                       | Estado     | Notas                                            |
| -------------------------- | ---------- | ------------------------------------------------ |
| 1. Foundation              | Completada | Validaciones de runtime pendientes (ver abajo)   |
| 2. Core ML Pipeline        | Completada | Validaciones de runtime pendientes               |
| 3. Pipeline Integration    | Completada | Validaciones de runtime pendientes               |
| 4. Production Infra        | Completada | Validaciones de runtime pendientes               |
| 5. Frontend (Mobile + Web) | Completada | UX testing con usuarios reales pendiente         |
| 6. Hardening               | Pendiente  |                                                  |

---

## Validaciones Pendientes de Runtime

Estas validaciones requieren Docker corriendo y deben ejecutarse antes de considerar cada fase completada al 100%. Ver detalle completo en `docs/plan/PENDING_VALIDATIONS.md`.

### Fase 1 — Foundation

- [ ] `make up` — verificar que todos los servicios suben
- [ ] `make migrate` — generar y ejecutar primera migracion de Alembic
- [ ] `curl http://localhost:8000/health` responde 200
- [ ] `curl http://localhost:8000/ready` responde 200 con todos los checks en true
- [ ] `make test` — todos los tests pasan
- [ ] `make lint` y `make typecheck` sin errores
- [ ] MinIO tiene los 3 buckets creados (selfie-images, document-images, processed-images)

### Fase 2 — Core ML Pipeline

- [ ] `make test-unit` — 108+ tests pasan (doc_processing, ocr, liveness, face_match, ml_tasks)
- [ ] `bash scripts/download-models.sh` — modelos ONNX descargados
- [ ] Tiempos de inferencia: doc_processing < 2s, OCR < 2s, liveness < 2s, face_match < 500ms
- [ ] Celery worker procesa tareas de las colas `cpu` y `gpu`

### Fase 3 — Pipeline Integration

- [ ] Pipeline end-to-end: `POST /api/v1/verification/start` con datos reales
- [ ] Timeout de 8 segundos funciona
- [ ] Degradacion graceful (liveness falla → MANUAL_REVIEW, OCR falla → penalizacion)
- [ ] Audit trail completo con PII anonimizado

### Fase 4 — Production Infrastructure

- [ ] Nginx proxea a FastAPI con TLS
- [ ] Rate limiting funciona (60 req/min general, 10 req/min verify)
- [ ] Dashboards Grafana cargan datos de Prometheus
- [ ] Trazas visibles en Jaeger con trace_id correlacionado
- [ ] Circuit breakers ante fallos de dependencias
- [ ] Helm chart valida: `helm template verifid infra/k8s/`
