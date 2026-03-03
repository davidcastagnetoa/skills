# ADR-004: PostgreSQL 16 + Patroni para persistencia

- **Estado**: accepted
- **Fecha**: 2026-03-03
- **Autores**: software-architecture-agent

## Contexto

El sistema necesita una base de datos relacional para almacenar sesiones de verificacion, resultados por modulo, logs de auditoria, listas negras de documentos y configuracion de clientes API. Los datos son estructurados con relaciones claras (sesion → resultados). Se requiere alta disponibilidad (> 99.9%) y la capacidad de recuperar datos ante fallos (PITR).

## Opciones Evaluadas

### Opcion A: PostgreSQL 16 + Patroni (HA)
- Pros: RDBMS mas avanzado del mercado, JSONB nativo para datos semi-estructurados, tipos nativos (UUID, INET, TIMESTAMPTZ), excelente query planner, replicacion streaming, Patroni para failover automatico, pgBackRest para backups, ecosistema maduro de herramientas (PgBouncer, pg_stat_statements).
- Contras: escalar escrituras horizontalmente requiere sharding manual o Citus, failover con Patroni agrega complejidad operativa.

### Opcion B: CockroachDB
- Pros: SQL distribuido, escala horizontal nativa, tolerancia a fallos sin Patroni, compatible con PostgreSQL wire protocol.
- Contras: latencia mayor por consenso distribuido, menos maduro que PostgreSQL, no soporta todas las extensiones PG (pgcrypto, pg_stat_statements), mayor consumo de recursos, menor comunidad.

### Opcion C: MySQL 8
- Pros: amplia adopcion, buena performance en lecturas, InnoDB es confiable.
- Contras: tipos de datos menos avanzados (sin JSONB nativo, sin INET, sin UUID nativo), transacciones menos robustas en edge cases, replicacion menos flexible que PostgreSQL.

### Opcion D: MongoDB
- Pros: schema-less, facil de empezar, escala horizontal nativa.
- Contras: los datos del sistema KYC son inherentemente relacionales (sesion → resultados → auditoria), falta de transacciones ACID completas entre colecciones, no es ideal para datos que requieren integridad referencial estricta.

## Decision

**PostgreSQL 16** como base de datos principal con **Patroni** para alta disponibilidad, **PgBouncer** para connection pooling y **pgBackRest** para backups.

PostgreSQL es la eleccion natural para datos estructurados con relaciones claras. JSONB permite flexibilidad para campos como metadata y details sin sacrificar las garantias ACID. La combinacion Patroni + PgBouncer + pgBackRest es el stack de produccion mas probado para PostgreSQL en Kubernetes.

## Consecuencias

- Se usa SQLAlchemy 2.0 async como ORM con asyncpg como driver (maximo rendimiento async).
- PgBouncer en modo transaction pooling reduce conexiones al backend de ~200 (workers) a ~20 reales.
- Patroni requiere etcd (3 nodos) como consensus store; esto agrega 3 contenedores extra en produccion.
- pgBackRest almacena backups cifrados en MinIO (S3-compatible), con retencion de 4 full (1 mes) + 14 diferenciales.
- Las migraciones de esquema se gestionan con Alembic y se ejecutan automaticamente en el CI/CD antes de cada despliegue.
- En desarrollo local se usa un unico nodo PostgreSQL sin Patroni para simplicidad.
