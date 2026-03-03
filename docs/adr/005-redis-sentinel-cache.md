# ADR-005: Redis 7 + Sentinel para cache y rate limiting

- **Estado**: accepted
- **Fecha**: 2026-03-03
- **Autores**: software-architecture-agent

## Contexto

El sistema necesita un almacen en memoria de baja latencia para multiples propositos: cache de sesiones activas, cache de resultados ML (embeddings, OCR), rate limiting por IP/dispositivo, contadores de intentos y broker de Celery. El acceso debe ser O(1) y la latencia < 1ms para no penalizar el pipeline de 8 segundos.

## Opciones Evaluadas

### Opcion A: Redis 7 + Sentinel
- Pros: latencia < 1ms, estructuras de datos ricas (strings, hashes, sorted sets para sliding window), TTL nativo, persistencia RDB + AOF, Sentinel para failover automatico, un solo servicio para cache + rate limiting + broker.
- Contras: toda la data en memoria (coste), Sentinel es HA sin sharding (escalado vertical).

### Opcion B: Redis 7 + Cluster
- Pros: sharding horizontal automatico, mayor capacidad.
- Contras: mayor complejidad operativa, algunas operaciones multi-key no funcionan entre slots, overkill para el volumen esperado del sistema KYC.

### Opcion C: Memcached
- Pros: simple, probado, multi-threaded.
- Contras: solo key-value simple (sin sorted sets para rate limiting), sin persistencia, sin pub/sub, no puede servir como broker de Celery, se necesitarian dos servicios (Memcached + Redis/RabbitMQ).

### Opcion D: Valkey
- Pros: fork open-source de Redis, compatible, mantenido por Linux Foundation.
- Contras: comunidad mas pequena, menor madurez en produccion, menos documentacion disponible.

## Decision

**Redis 7 con Sentinel** para alta disponibilidad. Un unico servicio Redis cubre cache, rate limiting y broker de Celery.

Sentinel proporciona failover automatico con 1 primary + N replicas, suficiente para el volumen esperado. Si el sistema crece mas alla de la capacidad de un nodo Redis (~25GB), se migrara a Redis Cluster (la API de redis-py es compatible, el cambio es de configuracion).

## Consecuencias

- Persistencia configurada con RDB (snapshots cada 5 min) + AOF (append every second) para balance entre rendimiento y durabilidad.
- Eviction policy `allkeys-lru` con max memory 256MB en desarrollo, ajustable en produccion.
- Todas las claves de cache tienen TTL explicito (5-15 min para sesiones, 1 hora para geo, 5 min para blacklists).
- Rate limiting usa sorted sets con sliding window (O(log N) por operacion).
- En desarrollo local se usa un unico nodo Redis sin Sentinel.
- El cliente Python es `redis-py` async con hiredis para maxima performance.
