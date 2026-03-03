---
name: pydantic_v2
description: Validación y serialización ultra-rápida de contratos de datos entre agentes
type: Library
priority: Esencial
mode: Self-hosted
---

# pydantic_v2

Pydantic v2 (core en Rust) define los contratos entre agentes como modelos tipados, garantizando integridad de datos en cada transición del pipeline.

## When to use

Usar para todos los modelos de entrada/salida, payloads de Celery, respuestas de API y eventos de auditoría.

## Instructions

1. Instalar: `pip install pydantic>=2.0`
2. Definir modelos en `backend/schemas/` heredando de `BaseModel`.
3. Usar `model_validator` para validaciones cross-field.
4. Usar `Field(strict=True)` para tipos que no deben hacer coerción.
5. Serializar: `.model_dump()`, deserializar: `Model.model_validate(data)`.
6. Versionar schemas: `VerificationRequestV1`, `VerificationRequestV2`.
7. Mantener schema registry en `backend/schemas/__init__.py`.

## Notes

- v2 es 5-50x más rápido que v1 gracias al core en Rust.
- `model_config = ConfigDict(frozen=True)` para modelos inmutables.
- Usar `Annotated` con `Field` para documentación OpenAPI automática.