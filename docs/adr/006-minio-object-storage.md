# ADR-006: MinIO como object storage self-hosted

- **Estado**: accepted
- **Fecha**: 2026-03-03
- **Autores**: software-architecture-agent

## Contexto

El sistema almacena temporalmente imagenes de selfies, documentos de identidad e imagenes procesadas durante el pipeline de verificacion. Las imagenes son datos biometricos sensibles que deben cifrarse, almacenarse de forma segura y eliminarse automaticamente tras 15 minutos (GDPR). Se necesita un almacen de objetos compatible con S3 para desacoplar el almacenamiento de la logica de negocio.

## Opciones Evaluadas

### Opcion A: MinIO (self-hosted, S3-compatible)
- Pros: S3 API compatible (mismos SDKs), self-hosted (datos bajo control total), open-source, ligero, soporta cifrado server-side, versionado de objetos, politicas de retencion, facil de desplegar en Docker/K8s, sin costes por transferencia.
- Contras: requiere gestion operativa (backups, HA, monitoring), no tiene CDN integrada.

### Opcion B: AWS S3
- Pros: managed (sin operaciones), escalabilidad infinita, alta durabilidad (11 nueves), CDN con CloudFront, lifecycle policies nativas.
- Contras: datos biometricos salen del perimetro de la empresa, coste por transferencia, dependencia de vendor, requiere configuracion IAM, latencia de red.

### Opcion C: Almacenamiento local (filesystem)
- Pros: sin dependencias adicionales, latencia minima.
- Contras: no escala horizontalmente, no hay API estandar, dificil de gestionar en multiples nodos K8s, sin cifrado nativo, sin lifecycle policies.

## Decision

**MinIO self-hosted** como object storage principal.

La prioridad del sistema es mantener los datos biometricos bajo control total. MinIO proporciona una API S3-compatible que permite migrar a AWS S3 en el futuro sin cambiar el codigo (mismos SDKs). Al ser self-hosted, los datos nunca salen del perimetro de la infraestructura.

## Consecuencias

- Las imagenes se cifran con AES-256-GCM antes de subir a MinIO (cifrado client-side, clave en Vault).
- Se crean 3 buckets: `selfie-images`, `document-images`, `processed-images`.
- Un job de Celery Beat purga imagenes con > 15 min de antiguedad cada 5 minutos.
- MinIO se despliega con persistencia en volumen Docker (desarrollo) o PVC en K8s (produccion).
- Si en el futuro se necesita CDN o escala masiva, la migracion a S3 requiere solo cambiar la configuracion del endpoint (la API es identica).
- pgBackRest tambien usa MinIO como repositorio de backups de PostgreSQL.
