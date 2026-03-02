---
name: nginx_lua
description: Reverse proxy de alto rendimiento con módulo Lua para lógica personalizada de gateway
---

# nginx_lua

Nginx con OpenResty (módulo LuaJIT integrado) actúa como API Gateway principal. Gestiona TLS termination, routing, rate limiting distribuido via Redis, y permite lógica personalizada en Lua sin recompilar Nginx.

## When to use

Usar como punto de entrada único a todos los microservicios KYC. Todo el tráfico externo pasa por Nginx — nunca exponer los servicios FastAPI directamente a internet.

## Instructions

1. Usar imagen OpenResty: `docker pull openresty/openresty:alpine`
2. Configuración base en `nginx/conf/nginx.conf`:
   ```nginx
   upstream kyc_api {
       least_conn;
       server kyc-api-1:8000;
       server kyc-api-2:8000;
       keepalive 32;
   }
   server {
       listen 443 ssl http2;
       ssl_certificate /etc/ssl/certs/kyc.crt;
       ssl_certificate_key /etc/ssl/private/kyc.key;
       ssl_protocols TLSv1.3;
       ssl_ciphers TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256;
       client_max_body_size 20M;  # máximo payload (2 imágenes ~5MB c/u + overhead)
       location /v1/ {
           proxy_pass http://kyc_api;
           proxy_http_version 1.1;
           proxy_set_header Connection "";
           proxy_read_timeout 30s;
       }
   }
   ```
3. Añadir security headers en `add_header` block (ver skill `security_headers`).
4. Habilitar Gzip: `gzip on; gzip_types application/json; gzip_min_length 1024;`
5. Configurar access log en formato JSON para ingesta por Promtail.
6. Rate limiting con módulo `limit_req_zone` + Redis via lua-resty-redis para contadores distribuidos.
7. Healthcheck: `location /health { return 200 "ok"; access_log off; }`

## Notes

- OpenResty incluye LuaJIT — soporta hasta 50K req/s por instancia en hardware moderno.
- Nunca exponer el puerto 8000 de FastAPI al exterior — solo el 443 de Nginx.
- Rotar certificados TLS con cert-manager automáticamente — Nginx recarga con `nginx -s reload`.