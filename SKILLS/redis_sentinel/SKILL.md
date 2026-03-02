---
name: redis_sentinel
description: Redis 7 con Sentinel para caché, rate limiting y sesiones con alta disponibilidad
---

# redis_sentinel

Redis es el caché central del sistema: sesiones activas, embeddings cacheados, listas negras, configuración dinámica y rate limiting. Redis Sentinel garantiza HA con failover automático.

## When to use

Usar para todos los datos de acceso frecuente que no requieren persistencia duradera: sesiones KYC, rate limits, configuración, blacklists.

## Instructions

1. Desplegar Redis con Sentinel: 1 master + 2 replicas + 3 sentinels (mínimo para quorum).
2. Configurar con Docker Compose o Helm chart `bitnami/redis`.
3. Conectar desde Python con `redis-py` con soporte Sentinel:
   ```python
   from redis.sentinel import Sentinel
   sentinel = Sentinel([('sentinel1', 26379), ('sentinel2', 26379)], socket_timeout=0.1)
   redis_master = sentinel.master_for('mymaster', socket_timeout=0.1)
   redis_slave = sentinel.slave_for('mymaster', socket_timeout=0.1)
   ```
4. Usar `redis_master` para escrituras, `redis_slave` para lecturas.
5. Configurar `maxmemory-policy allkeys-lru` para evitar OOM.
6. Encriptar conexiones con TLS: `redis-cli --tls`.

## Notes

- Para caché de embeddings: `SET embed:{doc_id} {embedding_b64} EX 3600`.
- Redis Cluster es alternativa si se necesita sharding horizontal (más de 1 nodo master).