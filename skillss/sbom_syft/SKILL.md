---
name: sbom_syft
description: Generar inventario de todas las dependencias del sistema (Software Bill of Materials) para auditorías de seguridad
---

# sbom_syft

Syft genera un SBOM (Software Bill of Materials) — un inventario completo y legible por máquinas de todas las dependencias incluidas en las imágenes Docker. Es requerido por regulaciones de seguridad de software (Executive Order 14028) y útil para responder rápidamente ante nuevas CVEs.

## When to use

Generar en el pipeline de CI tras cada build de imagen Docker. Almacenar el SBOM junto al release tag para poder auditarlo posteriormente.

## Instructions

1. Instalar: `brew install syft` o `curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh`.
2. Generar SBOM en formato SPDX-JSON: `syft kyc-api:v1.2.3 -o spdx-json > sbom-v1.2.3.spdx.json`.
3. Integrar en GitHub Actions:
   ```yaml
   - name: Generate SBOM
     uses: anchore/sbom-action@v0
     with:
       image: kyc-api:${{ github.sha }}
       format: spdx-json
       output-file: sbom.spdx.json
   - name: Upload SBOM
     uses: actions/upload-artifact@v3
     with: { name: sbom, path: sbom.spdx.json }
   ```
4. Combinar con Grype para escanear el SBOM en busca de CVEs: `grype sbom:sbom.spdx.json`.
5. Publicar el SBOM en el GitHub Release como asset adjunto.

## Notes

- El SBOM permite responder en minutos a preguntas como "¿estamos afectados por Log4Shell?" — búsqueda en el inventario en lugar de revisar cada imagen manualmente.
- Syft detecta dependencias de sistema operativo (apt), Python (pip), Node.js (npm) y más.