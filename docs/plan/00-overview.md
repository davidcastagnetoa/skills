# Plan de Desarrollo - VerifID (KYC Identity Verification System)

## Resumen Ejecutivo

Sistema de verificación de identidad (KYC) que compara un documento de identidad con una selfie en tiempo real para confirmar la identidad del usuario. Self-hosted, resistente a fraudes, con < 8s de respuesta total.

---

## Indice de Fases

| Fase | Archivo | Descripcion | Dependencias |
|------|---------|-------------|--------------|
| 1 | [01-foundation.md](./01-foundation.md) | Cimientos: scaffolding, Docker, BBDD, cache, API base | Ninguna |
| 2 | [02-core-ml-pipeline.md](./02-core-ml-pipeline.md) | Pipeline ML: liveness, face match, doc processing, OCR | Fase 1 |
| 3 | [03-pipeline-integration.md](./03-pipeline-integration.md) | Integracion: orquestador, antifraude, decision, auditoria | Fase 1 + 2 |
| 4 | [04-production-infra.md](./04-production-infra.md) | Produccion: API Gateway, observabilidad, seguridad, HA, K8s | Fase 1 + 3 |
| 5 | [05-frontend.md](./05-frontend.md) | Frontend: app movil (React Native), web, UX de captura | Fase 3 |
| 6 | [06-hardening.md](./06-hardening.md) | Endurecimiento: chaos engineering, performance, compliance | Fase 4 + 5 |

---

## Diagrama de Dependencias entre Fases

```
Fase 1 (Foundation)
  ├──> Fase 2 (Core ML Pipeline)
  │       └──> Fase 3 (Pipeline Integration)
  │               ├──> Fase 4 (Production Infra)
  │               │       └──> Fase 6 (Hardening)
  │               └──> Fase 5 (Frontend)
  │                       └──> Fase 6 (Hardening)
  └──> Fase 4 (Production Infra) [parcialmente paralela con Fase 2-3]
```

---

## Mapa de Agentes por Fase

### Fase 1 - Foundation
- `database-agent` — PostgreSQL 16, PgBouncer, Alembic
- `cache-agent` — Redis 7, Sentinel
- `software-architecture-agent` — ADRs iniciales, contratos base

### Fase 2 - Core ML Pipeline
- `liveness-agent` — Anti-spoofing pasivo + activo
- `face-match-agent` — ArcFace, embeddings, similitud
- `document-processor-agent` — OpenCV, YOLOv8, ELA
- `ocr-agent` — PaddleOCR, MRZ parser
- `model-server-agent` — Triton/TorchServe, ONNX, TensorRT

### Fase 3 - Pipeline Integration
- `orchestrator-agent` — Flujo completo, paralelismo
- `antifraud-agent` — Reglas transversales, blacklists
- `decision-agent` — Motor de decision, pesos, hard rules
- `audit-agent` — Logging, GDPR, HMAC
- `worker-pool-agent` — Celery, colas por prioridad
- `capture-agent` — Validacion de calidad de captura

### Fase 4 - Production Infrastructure
- `api-gateway-agent` — Nginx/Traefik, TLS, JWT, rate limiting
- `observability-agent` — Prometheus, Grafana, Jaeger, OpenTelemetry
- `health-monitor-agent` — Health checks, circuit breakers, alertas
- `security-agent` — Vault, cifrado, RBAC, cert-manager

### Fase 5 - Frontend
- `capture-agent` — WebRTC, CameraX/AVFoundation (parte frontend)

### Fase 6 - Hardening
- `health-monitor-agent` — Chaos engineering
- `software-architecture-agent` — Fitness functions, tech debt
- `security-agent` — Penetration testing, GDPR audit
- `observability-agent` — SLO/SLA tracking

---

## Mapa de Skills por Agente

Cada agente tiene asociadas skills que se consultan durante el desarrollo. Ver los archivos de agentes en `.claude/agents/` para la lista completa de skills por agente.

---

## Criterios de Calidad Globales

| Metrica | Objetivo |
|---------|----------|
| FAR (False Acceptance Rate) | < 0.1% |
| FRR (False Rejection Rate) | < 5% |
| Tiempo de respuesta total | < 8 segundos |
| Tasa de deteccion de spoofing | > 99% |
| Disponibilidad del servicio | > 99.9% |
| Cobertura de tests unitarios | > 80% |

---

## Stack Tecnologico

| Capa | Tecnologia |
|------|-----------|
| Backend | Python 3.12, FastAPI, Celery |
| ML Serving | NVIDIA Triton / TorchServe |
| Face Recognition | InsightFace (ArcFace) |
| Liveness | Silent-Face-Anti-Spoofing + Challenge-Response |
| OCR | PaddleOCR / EasyOCR |
| Document Detection | OpenCV + YOLOv8 |
| Base de datos | PostgreSQL 16 + Patroni + pgBackRest |
| Cache / Broker | Redis 7 + Sentinel |
| Object Storage | MinIO (S3-compatible) |
| API Gateway | Nginx + Lua |
| Observabilidad | Prometheus + Grafana + Jaeger + OpenTelemetry |
| Secretos | HashiCorp Vault |
| Infraestructura | Docker + Kubernetes + Helm |
| CI/CD | GitHub Actions |
| Frontend | React Native (movil) + Web (React/WebRTC) |

---

## Convencion de Continuidad

Este plan esta dividido en archivos independientes por fase. Si una sesion se interrumpe por rate limit, consultar `docs/plan/` y continuar desde la ultima fase incompleta. Cada archivo de fase tiene sus propios checkpoints internos marcados con `[ ]` (pendiente) y `[x]` (completado) para rastrear el progreso.
