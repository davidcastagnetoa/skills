---
name: postgresql_sqlalchemy_async
description: ORM async moderno para persistencia de sesiones de auditoría, logs y listas negras
---

# postgresql_sqlalchemy_async

SQLAlchemy 2.0 en modo async es el ORM principal para todas las operaciones de base de datos. Se integra nativamente con FastAPI y asyncio, garantizando que las escrituras de auditoría no bloquean el pipeline KYC.

## When to use

Usar para todas las operaciones CRUD sobre PostgreSQL: insertar sesiones de auditoría, consultar listas negras, registrar decisiones, gestionar la cola de revisión manual.

## Instructions

1. Instalar: `pip install sqlalchemy[asyncio] asyncpg alembic`
2. Configurar engine async en `backend/db/engine.py`:
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
   from sqlalchemy.orm import sessionmaker
   engine = create_async_engine("postgresql+asyncpg://user:pass@pgbouncer:5432/kyc", pool_size=20)
   AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
   ```
3. Definir modelos en `backend/db/models/`:
   - `AuditSession`: session_id, user_id_hash, decision, global_score, agent_scores (JSONB), integrity_hash, created_at.
   - `BlacklistedDocument`: doc_number_hash, doc_type, country, reason, created_at.
   - `ManualReviewQueue`: session_id, reason, status, assigned_to, created_at.
4. Inyectar sesión DB en FastAPI via dependency: `async with AsyncSessionLocal() as session`.
5. Usar `session.add()` + `await session.commit()` — nunca commits síncronos.
6. Gestionar migraciones con Alembic: `alembic upgrade head` en el init del contenedor.
7. Conectar siempre a través de PgBouncer (puerto 5432) — nunca directo al puerto 5433 de PostgreSQL.

## Notes

- `expire_on_commit=False` es obligatorio en async para evitar lazy loading tras el commit.
- Los INSERTs de auditoría deben ser fire-and-forget: usar `asyncio.create_task()` para no bloquear la respuesta al cliente.
- Nunca almacenar embeddings faciales en PostgreSQL — usar MinIO con TTL corto.