---
name: testcontainers
description: Levantar dependencias reales en contenedores para tests de integración reproducibles
type: Tool
priority: Esencial
mode: Self-hosted
---

# testcontainers

Testcontainers levanta instancias reales de PostgreSQL, Redis y MinIO como contenedores Docker durante los tests de integración. Esto elimina los mocks frágiles y garantiza que el código funciona con las dependencias reales.

## When to use

Usar en los tests de integración donde se necesita verificar comportamiento real: que los logs se persisten correctamente en PostgreSQL, que el rate limiter funciona con Redis real, que las imágenes se suben y se recuperan de MinIO.

## Instructions

1. Instalar: `pip install testcontainers[postgresql,redis]`
2. Fixture de PostgreSQL en `conftest.py`:
   ```python
   import pytest
   from testcontainers.postgres import PostgresContainer
   @pytest.fixture(scope="session")
   def postgres_container():
       with PostgresContainer("postgres:16-alpine") as pg:
           yield pg.get_connection_url().replace("postgresql://", "postgresql+asyncpg://")
   ```
3. Fixture de Redis:
   ```python
   from testcontainers.redis import RedisContainer
   @pytest.fixture(scope="session")
   def redis_container():
       with RedisContainer("redis:7-alpine") as r:
           yield f"redis://{r.get_container_host_ip()}:{r.get_exposed_port(6379)}"
   ```
4. Usar en tests: pasar las URLs de conexión como variables de entorno al setup de la app.
5. `scope="session"` reutiliza el mismo contenedor para todos los tests de la sesión — evita recrear el contenedor en cada test (lento).
6. Las migraciones Alembic deben ejecutarse contra el contenedor antes de los tests: `alembic upgrade head`.

## Notes

- Testcontainers requiere Docker disponible en el entorno de CI — usar GitHub Actions con `runs-on: ubuntu-latest` que incluye Docker.
- Para tests de modelos ML, no usar Testcontainers para el model server — mockear las respuestas de inferencia en tests unitarios y tener tests de integración separados que requieran GPU.
- El contenedor se destruye automáticamente al finalizar la fixture — no hay cleanup manual necesario.