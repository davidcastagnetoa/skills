---
name: security_headers
description: Headers de seguridad HTTP obligatorios para proteger el frontend KYC de ataques comunes
type: Protocol
priority: Esencial
mode: Self-hosted
---

# security_headers

Los security headers instruyen al browser a aplicar restricciones de seguridad que mitigan XSS, clickjacking, MIME sniffing y otros ataques. Son la primera línea de defensa del lado cliente y son requeridos por estándares como OWASP ASVS nivel 2.

## When to use

Añadir en Nginx para todas las respuestas del API y del frontend. Verificar con herramientas como securityheaders.com o OWASP ZAP antes de cada release.

## Instructions

1. Añadir en el bloque `server` de Nginx:
   ```nginx
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-Frame-Options "DENY" always;
   add_header Referrer-Policy "strict-origin-when-cross-origin" always;
   add_header Permissions-Policy "camera=(self), microphone=(self), geolocation=()" always;
   add_header Content-Security-Policy "default-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none';" always;
   ```
2. `Permissions-Policy`: `camera=(self)` y `microphone=(self)` son críticos — permiten acceso WebRTC solo desde el propio dominio.
3. `Content-Security-Policy`: ajustar según las fuentes reales del frontend (fonts, scripts externos si los hubiera).
4. `HSTS preload`: una vez configurado, se puede añadir el dominio a la HSTS preload list de los browsers.
5. Verificar que los headers `always` se envían también en respuestas de error (4xx, 5xx).
6. Incluir test automatizado en CI con `pytest` + `requests` que verifique la presencia de cada header.

## Notes

- `X-Frame-Options: DENY` previene ataques de clickjacking donde se embebe el formulario KYC en un iframe malicioso.
- Para WebRTC (capture_agent), `Permissions-Policy: camera=(self)` es imprescindible — sin él el browser puede bloquear el acceso a cámara.
- Revisar la CSP con Report-Only mode antes de activarla en producción para no romper assets legítimos.