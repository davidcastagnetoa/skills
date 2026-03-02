---
name: minio_object_storage
description: Object storage S3-compatible self-hosted para almacenamiento temporal cifrado de imágenes biométricas
---

# minio_object_storage

MinIO almacena temporalmente las imágenes de selfie y documento durante el tiempo de vida de la sesión KYC. Todo el almacenamiento es cifrado en reposo (AES-256) y los objetos se eliminan automáticamente al expirar el TTL definido por política GDPR.

## When to use

Usar al recibir las imágenes del cliente: guardar en MinIO antes de iniciar el pipeline, referenciarlas por `session_id/image_type.jpg` en todos los agentes, y eliminarlas automáticamente vía lifecycle policy.

## Instructions

1. Arrancar MinIO con Docker Compose:
   ```yaml
   minio:
     image: minio/minio:latest
     command: server /data --console-address ":9001"
     environment:
       MINIO_ROOT_USER: ${MINIO_USER}
       MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
       MINIO_KMS_SECRET_KEY: kyc-key:${MINIO_KMS_KEY_BASE64}
   ```
2. Instalar cliente Python: `pip install minio aiobotocore`
3. Crear bucket `kyc-sessions` con Server-Side Encryption habilitado.
4. Configurar lifecycle policy para eliminar objetos tras 24 horas:
   ```json
   {"Rules": [{"Status": "Enabled", "Expiration": {"Days": 1}, "Filter": {"Prefix": ""}}]}
   ```
5. Subir imagen: `minio_client.put_object("kyc-sessions", f"{session_id}/selfie.jpg", data, length, content_type="image/jpeg")`.
6. Generar presigned URL de 15 minutos para que los agentes accedan sin exponer credenciales.
7. Forzar borrado manual al completar la sesión además del lifecycle automático.

## Notes

- Nunca servir las imágenes directamente al frontend — solo acceso interno entre agentes.
- El bucket debe tener Block Public Access activado.
- Hacer backup del bucket de configuración, no del de sesiones (datos efímeros).
- En producción usar MinIO Distributed Mode (4+ nodos) para HA.