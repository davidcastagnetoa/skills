---
name: rate_limiting_gateway
description: Control de tasa por IP en el API Gateway con ventana deslizante implementada en Redis
---

# rate_limiting_gateway

El rate limiting en el gateway es la defensa primaria contra ataques de fuerza bruta, scraping y credential stuffing. Se implementa con ventana deslizante en Redis para ser preciso y distribuido entre múltiples instancias de Nginx.

## When to use

Aplicar en todos los endpoints del API. Los límites del gateway son más laxos que los del antifraud_agent (que aplica límites específicos por documento/dispositivo).

## Instructions

1. Usar `ngx_http_limit_req_module` de Nginx para rate limiting simple:
   ```nginx
   limit_req_zone $binary_remote_addr zone=kyc_api:10m rate=10r/s;
   limit_req zone=kyc_api burst=20 nodelay;
   limit_req_status 429;
   ```
2. Para rate limiting distribuido entre instancias, usar lua-resty-limit-traffic con Redis:
   ```lua
   local limit_req = require "resty.limit.req"
   local lim = limit_req.new("redis_pool", 10, 20)  -- 10 req/s, burst 20
   local delay, err = lim:incoming(ngx.var.binary_remote_addr, true)
   if not delay then
       if err == "rejected" then ngx.exit(429) end
   end
   ```
3. Límites por endpoint:
   - `POST /v1/verify` (inicio de sesión KYC): 5 req/min por IP.
   - `GET /v1/status/{session_id}`: 30 req/min por IP.
   - `GET /health`: sin límite.
4. Devolver header `Retry-After` con el tiempo de espera en respuestas 429.
5. Logear todos los 429 con IP y endpoint — son señal de ataque o cliente mal programado.

## Notes

- El rate limiting del gateway es por IP. El del antifraud_agent es por documento/dispositivo — son capas complementarias.
- Las IPs que generan 429 repetidamente deben escalarse a la blacklist tras N violaciones.
- En Kubernetes con múltiples pods de Nginx, el Redis compartido garantiza que el límite sea global.