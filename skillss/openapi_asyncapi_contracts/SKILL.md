---
name: openapi_asyncapi_contracts
description: Definir y versionar contratos de interfaz entre agentes REST (OpenAPI) y asíncronos (AsyncAPI)
---

# openapi_asyncapi_contracts

Los contratos entre agentes definen los schemas de datos que cada agente acepta y produce. Son la fuente única de verdad para comunicación inter-agente y previenen breaking changes.

## When to use

Usar para documentar y versionar todos los contratos entre agentes: endpoints REST, payloads de Celery y eventos de auditoría.

## Instructions

1. FastAPI genera OpenAPI automáticamente en `/openapi.json`; verificar que está completo y correcto.
2. Versionar el `openapi.json` en Git: comparar con la versión anterior en cada PR.
3. Para mensajes asíncronos de Celery, definir contratos en AsyncAPI 2.x:
   - Crear `asyncapi.yaml` en `docs/contracts/`.
   - Documentar cada canal (cola Celery) con su schema de mensaje.
4. Implementar un breaking change detector en CI:
   - `pip install openapi-spec-validator oasdiff`.
   - `oasdiff breaking old_spec.yaml new_spec.yaml` → falla el CI si hay breaking changes.
5. Usar Pydantic models como fuente única de verdad y generar los specs desde el código.

## Notes

- AsyncAPI playground: https://studio.asyncapi.com
- `oasdiff`: https://github.com/Tufin/oasdiff — detección de breaking changes en CI.