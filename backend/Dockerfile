# ============================================================
# VerifID Backend — Multi-stage Dockerfile
# ============================================================

# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# --- Stage 2: Runtime ---
FROM python:3.12-slim AS runtime

RUN groupadd -r verifid && useradd -r -g verifid -d /app -s /sbin/nologin verifid

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . /app/

RUN chown -R verifid:verifid /app

USER verifid

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
