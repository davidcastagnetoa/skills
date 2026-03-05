# VerifID — Deployment Guide

## Local Development

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Generate self-signed TLS certs
chmod +x infra/nginx/ssl/generate-dev-certs.sh
./infra/nginx/ssl/generate-dev-certs.sh

# 3. Start all services
cd infra/docker
docker compose up -d

# 4. Access services
#    API:        http://localhost:8000
#    Nginx:      https://localhost:443
#    Grafana:    http://localhost:3000  (admin / verifid)
#    Prometheus: http://localhost:9090
#    Jaeger:     http://localhost:16686
#    MinIO:      http://localhost:9001  (minioadmin / minioadmin)
```

## High Availability (PostgreSQL)

```bash
# Start with HA overlay
cd infra/docker
docker compose -f docker-compose.yml -f docker-compose.ha.yml up -d

# PgBouncer is available at localhost:6432
# Update DATABASE_URL to use PgBouncer:
#   postgresql+asyncpg://verifid:verifid_secret@localhost:6432/verifid
```

## Kubernetes Deployment

```bash
# Staging
helm install verifid infra/k8s/ \
  -f infra/k8s/values.yaml \
  -f infra/k8s/values-staging.yaml \
  -n verifid-staging --create-namespace

# Production
helm install verifid infra/k8s/ \
  -f infra/k8s/values.yaml \
  -f infra/k8s/values-production.yaml \
  -n verifid-prod --create-namespace

# Upgrade
helm upgrade verifid infra/k8s/ \
  -f infra/k8s/values.yaml \
  -f infra/k8s/values-production.yaml \
  -n verifid-prod
```

## Pre-requisites for Production

1. **Secrets**: Use SealedSecrets or External Secrets Operator (do NOT use the template secret.yaml with real values)
2. **TLS**: Configure cert-manager with a ClusterIssuer for Let's Encrypt
3. **GPU**: Ensure NVIDIA device plugin is installed for Triton
4. **Storage**: Provision PersistentVolumes for PostgreSQL, Redis, MinIO
5. **Vault**: Deploy HashiCorp Vault and populate secrets

## CI/CD

PRs trigger the GitHub Actions CI pipeline automatically:
- **lint**: ruff + black + mypy
- **test**: pytest with PostgreSQL + Redis services
- **security**: bandit + pip-audit
- **build**: Docker image build + Trivy scan
- **schema**: OpenAPI schema validation

Releases follow semantic versioning via conventional commits.
