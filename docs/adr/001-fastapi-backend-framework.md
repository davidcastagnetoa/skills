# ADR-001: FastAPI como framework backend

- **Estado**: accepted
- **Fecha**: 2026-03-03
- **Autores**: software-architecture-agent

## Contexto

El sistema KYC necesita un framework web Python que soporte procesamiento asincrono de alto rendimiento, ya que el pipeline involucra multiples llamadas concurrentes a modelos ML, bases de datos y servicios de almacenamiento. El tiempo de respuesta total debe ser inferior a 8 segundos, lo que requiere paralelismo real entre modulos independientes (liveness + doc_processing en paralelo, face_match + OCR en paralelo).

## Opciones Evaluadas

### Opcion A: FastAPI
- Pros: async nativo (ASGI), tipado con Pydantic integrado, auto-generacion de OpenAPI/Swagger, alto rendimiento (comparable a Go/Node), dependency injection nativo, amplia adopcion en ML/AI backends.
- Contras: ecosistema de plugins mas reducido que Django, no incluye ORM propio (requiere SQLAlchemy aparte).

### Opcion B: Django + Django REST Framework
- Pros: ecosistema maduro, ORM integrado, admin panel, migraciones nativas, amplia comunidad.
- Contras: sincrono por defecto (async aun experimental), overhead significativo para APIs puras, mas lento en benchmarks, tipado no nativo.

### Opcion C: Flask
- Pros: minimalista, flexible, gran ecosistema de extensiones.
- Contras: sincrono por defecto, sin tipado nativo, sin auto-documentacion de API, requiere muchas extensiones para equiparar funcionalidad.

## Decision

**FastAPI** como framework backend principal.

La naturaleza asincrona es critica para el pipeline KYC: el orquestador necesita ejecutar `asyncio.gather()` para paralelizar fases independientes y cumplir el SLO de 8 segundos. El tipado con Pydantic v2 garantiza validacion robusta de los contratos entre agentes. La auto-generacion de OpenAPI facilita la integracion con el frontend y la documentacion de la API.

## Consecuencias

- Todo el equipo debe estar familiarizado con programacion asincrona en Python (async/await).
- Se adopta SQLAlchemy 2.0 async como ORM (no viene incluido con FastAPI).
- Se adopta Pydantic v2 como unica libreria de validacion/serializacion.
- Si en el futuro se necesita un admin panel, se evaluara FastAPI-Admin o un servicio separado en lugar de migrar a Django.
