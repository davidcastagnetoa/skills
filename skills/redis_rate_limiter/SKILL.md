---
name: redis_rate_limiter
description: Control de intentos de verificación por IP/dispositivo/documento con ventana deslizante en Redis
type: Library
priority: Esencial
mode: Self-hosted
---

# redis_rate_limiter

Implementa rate limiting con algoritmo de ventana deslizante (sliding window) en Redis para limitar el número de intentos de verificación por IP, dispositivo y número de documento.

## When to use

Aplicar en el `api_gateway_agent` y `antifraud_agent` como primera línea de defensa contra ataques de fuerza bruta.

## Instructions

1. Instalar: `pip install redis`.
2. Algoritmo sliding window con sorted sets de Redis:
   - Key: `ratelimit:{type}:{identifier}` (ej. `ratelimit:ip:192.168.1.1`).
   - Añadir timestamp actual: `ZADD key {now_ms} {now_ms}`.
   - Eliminar entradas fuera de la ventana: `ZREMRANGEBYSCORE key 0 {now_ms - window_ms}`.
   - Contar: `count = ZCARD key`.
   - Si `count > limit`: rechazar. Si no: proceder.
   - Expirar key: `EXPIRE key {window_seconds}`.
3. Límites configurables: IP: 10 intentos/hora; device_id: 5 intentos/día; doc_number: 3 intentos/hora.
4. Devolver headers estándar: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.

## Notes

- Para alto rendimiento usar scripts Lua en Redis para atomicidad sin round-trips.
- Redis Sentinel garantiza que el rate limiter no sea SPOF.