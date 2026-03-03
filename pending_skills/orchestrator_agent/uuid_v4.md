---
name: uuid_v4
description: Generación de session_id únicos e irrepetibles
type: Algorithm
priority: Esencial
mode: Self-hosted
---

# uuid_v4

UUID v4 genera identificadores universalmente únicos de 128 bits usando entropía aleatoria criptográfica. Cada sesión de verificación KYC recibe un UUID v4 como `session_id` para trazabilidad completa del pipeline.

## When to use

Usar al inicio de cada sesión de verificación en el `orchestrator_agent` para generar el `session_id` que acompaña todos los eventos, logs y resultados del pipeline.

## Instructions

1. Importar: `from uuid import uuid4`.
2. Generar session_id al crear la sesión: `session_id = str(uuid4())`.
3. Propagar el `session_id` como campo obligatorio en todos los mensajes entre agentes.
4. Incluir el `session_id` en todos los logs de auditoría y trazas distribuidas.
5. Usar como clave primaria en la tabla `verification_sessions` de PostgreSQL.
6. Incluir en la respuesta al cliente: `{ session_id, status, confidence_score, ... }`.

## Notes

- UUID v4 tiene probabilidad de colisión de ~1 en 2^122; no requiere coordinación entre nodos.
- No usar UUID v1 (contiene MAC address y timestamp, filtración de información).
- Almacenar como `UUID` nativo en PostgreSQL, no como `VARCHAR(36)`.
