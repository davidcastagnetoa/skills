---
name: pgbouncer_asyncpg
description: Connection pooling PostgreSQL con PgBouncer y cliente async asyncpg para alto rendimiento
---

# pgbouncer_asyncpg

PgBouncer en modo transaction pooling reduce el coste de conexiones PostgreSQL de ~10ms a <0.1ms. `asyncpg` es el cliente async de PostgreSQL más rápido para Python.

## When to use

Usar para todas las operaciones de base de datos del sistema. Nunca conectar directamente a PostgreSQL desde los servicios.

## Instructions

1. Instalar asyncpg: `pip install asyncpg`.
2. Instalar PgBouncer: disponible en `apt install pgbouncer` o imagen Docker.
3. Configurar PgBouncer en modo transaction pooling (`pool_mode = transaction`).
4. Configurar pool size: `max_client_conn = 1000`, `default_pool_size = 20`.
5. Crear pool de conexiones en FastAPI startup:
   ```python
   pool = await asyncpg.create_pool(dsn=PGBOUNCER_DSN, min_size=5, max_size=20)
   ```
6. Usar el pool en cada operación: `async with pool.acquire() as conn: await conn.fetch(query)`.
7. Health check: verificar que PgBouncer responde y tiene conexiones disponibles.

## Notes

- PgBouncer NO soporta prepared statements en transaction mode; usar `$1, $2` placeholders nativos.
- Patroni gestiona el failover primary/replica de PostgreSQL.
- Alembic para migraciones: `pip install alembic`.