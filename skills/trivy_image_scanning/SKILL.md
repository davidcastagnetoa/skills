---
name: trivy_image_scanning
description: Escanear imágenes Docker en busca de vulnerabilidades CVE antes de desplegar
type: Tool
priority: Esencial
mode: Self-hosted
---

# trivy_image_scanning

Trivy escanea las imágenes Docker del sistema KYC en busca de vulnerabilidades conocidas (CVEs) en las dependencias del sistema operativo y en los paquetes Python. El escaneo se ejecuta en CI y bloquea el deploy si se detectan CVEs críticos.

## When to use

Ejecutar en el pipeline de CI después de hacer el `docker build`. También ejecutar periódicamente sobre las imágenes en producción (nuevas CVEs se descubren constantemente).

## Instructions

1. Instalar: `brew install trivy` o `docker pull aquasec/trivy`.
2. En GitHub Actions (integrado en el skill `github_actions_cicd`):
   ```yaml
   - name: Scan image
     uses: aquasecurity/trivy-action@master
     with:
       image-ref: "kyc-api:${{ github.sha }}"
       format: "table"
       exit-code: "1"
       severity: "CRITICAL,HIGH"
       ignore-unfixed: true
   ```
3. `ignore-unfixed: true` — ignora CVEs sin parche disponible (no hay nada que hacer).
4. `severity: CRITICAL,HIGH` — bloquear solo en severidades altas para reducir false positives.
5. Generar reporte SARIF para GitHub Security tab: `format: "sarif", output: "trivy-results.sarif"`.
6. Escaneo periódico en producción: CronJob en Kubernetes que escanea imágenes en el registry cada semana.
7. Configurar `.trivyignore` para CVEs aceptados con justificación documentada.

## Notes

- Una imagen base actualizada resuelve la mayoría de CVEs — usar `python:3.11-slim` y actualizarla mensualmente.
- Trivy también escanea filesystems, repos Git y configuraciones de Kubernetes — no solo imágenes.
- Los CVEs de dependencias Python se detectan analizando `requirements.txt` o `pip list` — complementar con `pip-audit`.