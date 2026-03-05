# Fase 4: Production Infrastructure

**Agentes involucrados**: `api-gateway-agent`, `observability-agent`, `health-monitor-agent`, `security-agent`, `database-agent`, `model-server-agent`

**Objetivo**: Preparar el sistema para produccion con API Gateway seguro, observabilidad completa, alta disponibilidad, gestion de secretos y despliegue en Kubernetes.

**Prerequisitos**: Fase 1 completada. Fase 3 en progreso o completada (puede desarrollarse parcialmente en paralelo).

---

## 4.1 API Gateway (Nginx + Lua)

**Agente**: `api-gateway-agent`
**Skills**: `nginx_lua`, `tls_1_3_termination`, `jwt_rs256_validation`, `oauth2_pkce`, `api_key_management`, `rate_limiting_gateway`, `security_headers`, `cors_policy`, `circuit_breaker_gateway`, `gzip_brotli_compression`, `access_log_json`, `waf_modsecurity`

### Tareas

- [x] Configurar Nginx como reverse proxy:
  - Terminacion TLS 1.3 con certificados Let's Encrypt (dev: self-signed).
  - Upstream hacia el servicio FastAPI.
  - HTTP/2 habilitado.

- [x] Implementar autenticacion en Nginx Lua:
  - Validacion de JWT (RS256) en cada request.
  - Validacion de API Keys para clientes server-to-server.
  - Cache de claves publicas JWT en shared memory.

- [x] Implementar rate limiting en Nginx:
  - Sliding window por IP: configurable (default 60 req/min).
  - Rate limit especifico para `/api/v1/verify`: 10 req/min por IP.
  - Headers de respuesta: X-RateLimit-Remaining, X-RateLimit-Reset.

- [x] Configurar headers de seguridad:
  ```nginx
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
  add_header X-Content-Type-Options "nosniff" always;
  add_header X-Frame-Options "DENY" always;
  add_header X-XSS-Protection "1; mode=block" always;
  add_header Content-Security-Policy "default-src 'self'" always;
  add_header Referrer-Policy "strict-origin-when-cross-origin" always;
  ```

- [x] Configurar CORS por entorno (development vs production).

- [x] Implementar circuit breaker por Lua:
  - Rastrear tasa de errores 5xx por upstream.
  - Abrir circuito si > 50% errores en ventana de 30s.
  - Retornar 503 con mensaje descriptivo cuando circuito abierto.

- [x] Configurar compresion gzip/brotli para respuestas JSON.

- [x] Configurar logging JSON estructurado por request.

- [x] Limitar tamano maximo de request body (10MB para imagenes).

- [x] Agregar Nginx al docker-compose y al Dockerfile.

### Checkpoint 4.1
> Resultado esperado: Nginx proxea al backend con TLS, JWT validation, rate limiting y headers de seguridad. Circuit breaker funciona ante fallos del upstream.

---

## 4.2 Observabilidad

**Agente**: `observability-agent`
**Skills**: `prometheus`, `prometheus_client`, `grafana`, `opentelemetry_sdk`, `jaeger`, `thanos`, `structlog`, `log_correlation`, `promtail_vector`, `w3c_trace_context`, `node_exporter`, `dcgm_exporter`

### Tareas

#### 4.2.1 Metricas (Prometheus + Grafana)

- [x] Instrumentar FastAPI con prometheus_client:
  ```python
  REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency', ['method', 'endpoint', 'status'])
  VERIFICATION_SCORE = Histogram('verification_score', 'Score distribution', ['module'])
  VERIFICATION_TOTAL = Counter('verification_total', 'Total verifications', ['status'])
  ACTIVE_SESSIONS = Gauge('active_sessions', 'Currently processing sessions')
  ```

- [x] Instrumentar cada modulo ML con metricas:
  - Latencia de inferencia por modelo.
  - Throughput (inferences/second).
  - Score distributions (histogramas).
  - Error rates.

- [x] Configurar Prometheus server en docker-compose:
  - Scrape targets: FastAPI, Celery workers, Redis exporter, PostgreSQL exporter, Node exporter.
  - Retention: 15 dias local.

- [x] Crear dashboards Grafana:
  - [x] **Dashboard: API Overview** — RPS, latencia p50/p95/p99, error rate, active sessions.
  - [x] **Dashboard: KYC Pipeline** — scores por modulo, distribucion de decisiones, tiempo por fase.
  - [x] **Dashboard: ML Models** — latencia de inferencia, GPU utilization, throughput.
  - [x] **Dashboard: Infrastructure** — CPU, memoria, disco, red por servicio.
  - [x] **Dashboard: Security** — rate limit hits, blocked IPs, JWT errors.

- [x] Configurar alerting rules en Prometheus:
  ```yaml
  groups:
    - name: verifid-alerts
      rules:
        - alert: HighErrorRate
          expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        - alert: HighLatency
          expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 8
        - alert: LowLivenessAccuracy
          expr: rate(verification_total{module="liveness",result="false_accept"}[1h]) > 0.001
  ```

#### 4.2.2 Trazabilidad Distribuida (OpenTelemetry + Jaeger)

- [x] Integrar OpenTelemetry SDK en FastAPI:
  - Auto-instrumentacion de HTTP requests.
  - Propagacion de trace context (W3C Trace Context).
  - Exportar spans a Jaeger.

- [x] Instrumentar el pipeline del orquestador:
  - Span por cada fase del pipeline.
  - Span por cada modulo ML.
  - Atributos: session_id, module_name, score.

- [x] Instrumentar Celery tasks con spans.

- [x] Configurar Jaeger en docker-compose.

- [x] Configurar sampling: 100% en dev, 10% en produccion.

#### 4.2.3 Logs Centralizados

- [x] Configurar structlog para JSON logging correlacionado:
  - Cada log incluye: session_id, trace_id, span_id, timestamp.
  - Niveles: DEBUG (dev only), INFO, WARNING, ERROR.

- [x] Configurar Promtail/Vector para recoleccion de logs.

- [x] Configurar log retention: ERROR 90 dias, INFO 30 dias, DEBUG 7 dias.

### Checkpoint 4.2
> Resultado esperado: Dashboards Grafana muestran metricas en tiempo real. Jaeger muestra flame graphs de sesiones. Logs correlacionados por session_id y trace_id.

---

## 4.3 Health Monitoring

**Agente**: `health-monitor-agent`
**Skills**: `http_health_check_probes`, `deep_health_check`, `circuit_breaker`, `alertmanager`, `watchdog_supervisor`, `graceful_degradation`

### Tareas

- [x] Implementar health checks profundos en `/ready`:
  ```python
  async def readiness_check():
      checks = {
          "postgresql": await check_db_connection(),
          "redis": await check_redis_connection(),
          "minio": await check_minio_connection(),
          "models_loaded": check_models_loaded(),
          "celery_workers": await check_celery_workers(),
      }
      all_healthy = all(checks.values())
      return {"status": "ready" if all_healthy else "not_ready", "checks": checks}
  ```

- [x] Implementar circuit breakers para dependencias externas:
  - PostgreSQL: open after 5 failures in 30s, half-open after 15s.
  - Redis: open after 3 failures in 15s, half-open after 10s.
  - MinIO: open after 3 failures in 15s, half-open after 10s.
  - Model server: open after 3 failures in 30s, half-open after 20s.

- [x] Configurar Alertmanager:
  - Routing: critico → PagerDuty/Slack inmediato, warning → email digest.
  - Agrupacion por servicio para evitar alert storms.
  - Silencing para mantenimiento planificado.

- [x] Implementar auto-recovery:
  - Watchdog que reinicia workers de Celery si no responden.
  - Reconexion automatica a PostgreSQL y Redis tras fallos transitorios.

### Checkpoint 4.3
> Resultado esperado: Health checks detectan dependencias caidas. Circuit breakers se abren/cierran correctamente. Alertas llegan al canal configurado.

---

## 4.4 Seguridad

**Agente**: `security-agent`
**Skills**: `hashicorp_vault`, `aes_256_gcm`, `encryption_tls`, `cert_manager`, `rbac`, `owasp_top10_mitigations`, `bandit_pip_audit`, `trivy_image_scanning`, `pii_anonymizer_presidio`

### Tareas

- [x] Configurar HashiCorp Vault (dev mode para local):
  - Almacenar: DB passwords, Redis password, MinIO keys, JWT private key, encryption keys.
  - Crear politicas de acceso por servicio (minimo privilegio).
  - Integracion con FastAPI settings para inyectar secretos al arrancar.

- [x] Implementar cifrado de imagenes en MinIO:
  - Cifrar con AES-256-GCM antes de upload.
  - Descifrar al download.
  - Clave de cifrado en Vault.

- [x] Configurar `.env.example` sin secretos reales (solo placeholders).

- [x] Ejecutar security scanning:
  - `bandit` para analisis estatico del codigo Python.
  - `pip-audit` para vulnerabilidades en dependencias.
  - `trivy` para escanear imagenes Docker.

- [x] Generar SBOM (Software Bill of Materials) con Syft.

- [x] Implementar RBAC basico para el API:
  - Roles: `admin`, `operator`, `reviewer`, `client`.
  - Admin: full access.
  - Operator: verificaciones + dashboards.
  - Reviewer: cola de revision manual.
  - Client: solo crear y consultar verificaciones.

### Checkpoint 4.4
> Resultado esperado: Secretos en Vault, no en .env. Imagenes cifradas en MinIO. Escaneo de seguridad sin vulnerabilidades criticas. RBAC funcional.

---

## 4.5 Alta Disponibilidad de Base de Datos

**Agente**: `database-agent`
**Skills**: `patroni`, `pgbackrest`, `pgbouncer`

### Tareas

- [x] Configurar Patroni para HA de PostgreSQL:
  - Cluster de 2+ nodos (primary + replica).
  - etcd como consensus store.
  - Failover automatico < 30s.
  - Replicacion sincrona para no perder datos de verificacion.

- [x] Configurar PgBouncer como connection pooler:
  - Modo transaction pooling.
  - Max connections por backend configurable.
  - Health check de conexiones.

- [x] Configurar pgBackRest para backups:
  - Full backup semanal.
  - Diferencial diario.
  - WAL archiving continuo a MinIO.
  - Cifrado de backups (AES-256-CBC).

- [x] Crear docker-compose.ha.yml con la topologia completa.

### Checkpoint 4.5
> Resultado esperado: Failover de PostgreSQL funciona sin perdida de datos. Backups se ejecutan y se pueden restaurar. PgBouncer reduce conexiones al backend.

---

## 4.6 Model Server (Triton / TorchServe)

**Agente**: `model-server-agent`
**Skills**: `triton_inference_server`, `onnx_runtime`, `tensorrt`, `dynamic_batching_triton`

### Tareas

- [x] Configurar NVIDIA Triton Inference Server (o TorchServe si no hay GPU NVIDIA):
  - Model repository con todos los modelos ONNX.
  - Batching dinamico habilitado.
  - Health check endpoint.

- [x] Crear configuracion por modelo:
  ```
  model_repository/
  ├── arcface/
  │   ├── config.pbtxt
  │   └── 1/model.onnx
  ├── anti_spoofing/
  │   ├── config.pbtxt
  │   └── 1/model.onnx
  ├── retinaface/
  │   ├── config.pbtxt
  │   └── 1/model.onnx
  └── ...
  ```

- [x] Migrar inferencia de los modulos (Fase 2) para usar Triton client en vez de ONNX Runtime local:
  - gRPC client para maxima performance.
  - Fallback a ONNX Runtime local si Triton no esta disponible.

- [x] Agregar Triton al docker-compose.

### Checkpoint 4.6
> Resultado esperado: Triton sirve todos los modelos con batching dinamico. Latencia de inferencia < 100ms por modelo. Fallback a ONNX Runtime funciona.

---

## 4.7 CI/CD Pipeline

**Agente**: `software-architecture-agent`
**Skills**: `github_actions_cicd`, `pre_commit_hooks`, `conventional_commits`, `semantic_release`

### Tareas

- [x] Crear `.github/workflows/ci.yml`:
  ```yaml
  jobs:
    lint:        # ruff, black --check, mypy
    test:        # pytest con cobertura
    security:    # bandit, pip-audit, trivy
    build:       # docker build
    schema:      # validar que schemas no tienen breaking changes
  ```

- [x] Configurar pre-commit hooks:
  - black (formatter)
  - ruff (linter)
  - mypy (type checker)
  - conventional-commits (commit message format)

- [x] Configurar semantic release para versionado automatico basado en conventional commits.

### Checkpoint 4.7
> Resultado esperado: PRs pasan por lint + test + security scan automaticamente. Pre-commit hooks previenen codigo malformado.

---

## 4.8 Kubernetes (Preparacion)

**Agente**: `software-architecture-agent`
**Skills**: `kubernetes_helm`, `docker_docker_compose`

### Tareas

- [x] Crear Helm chart basico en `infra/k8s/`:
  ```
  infra/k8s/
  ├── Chart.yaml
  ├── values.yaml
  ├── values-staging.yaml
  ├── values-production.yaml
  └── templates/
      ├── api-deployment.yaml
      ├── api-service.yaml
      ├── celery-worker-deployment.yaml
      ├── celery-beat-deployment.yaml
      ├── nginx-deployment.yaml
      ├── configmap.yaml
      ├── secret.yaml (sealed)
      ├── hpa.yaml
      └── ingress.yaml
  ```

- [x] Configurar HPA (Horizontal Pod Autoscaler) para API y Celery workers.

- [x] Configurar liveness/readiness probes en todos los deployments.

- [x] Documentar el proceso de despliegue en `docs/deployment.md`.

### Checkpoint 4.8
> Resultado esperado: `helm install` despliega el stack completo en un cluster K8s. HPA escala workers automaticamente.

---

## Criterios de Completitud de Fase 4

- [x] API Gateway con TLS, JWT, rate limiting y circuit breaker
- [x] Dashboards Grafana operativos con metricas de negocio y infra
- [x] Trazabilidad distribuida funcional (Jaeger)
- [x] Health checks y alertas configurados
- [x] Secretos en Vault, imagenes cifradas en MinIO
- [x] Escaneo de seguridad sin vulnerabilidades criticas
- [x] PostgreSQL HA con Patroni + backups con pgBackRest
- [x] Model server (Triton/TorchServe) sirviendo todos los modelos
- [x] CI/CD pipeline con lint + test + security + build
- [x] Helm chart para despliegue en K8s
