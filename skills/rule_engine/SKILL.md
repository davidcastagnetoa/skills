---
name: rule_engine
description: Motor de reglas de negocio configurables sin redeploy usando rule-engine o durable-rules
type: Library
priority: Recomendada
mode: Self-hosted
---

# rule_engine

Externaliza la lógica de negocio del orquestador en reglas configurables, permitiendo ajustar el comportamiento sin redeploy.

## When to use

Usar para lógica de decisión que cambia frecuentemente: umbrales, condiciones de revisión manual, reglas por tipo de documento.

## Instructions

1. Instalar: `pip install rule-engine`
2. Definir reglas como strings evaluables:
   ```python
   import rule_engine
   rule = rule_engine.Rule('liveness_score > 0.8 and face_match_score > 0.75')
   result = rule.matches({'liveness_score': 0.9, 'face_match_score': 0.82})
   ```
3. Almacenar definiciones de reglas en Redis o PostgreSQL.
4. Cargar reglas al arrancar y refrescar cada 60 segundos.
5. Implementar validación de sintaxis al guardar una nueva regla.
6. Versionar reglas con timestamp y autor para auditoría.
7. Endpoint admin: `POST /admin/rules` protegido con RBAC.

## Notes

- Alternativa: `durable-rules` — soporta reglas más complejas con estado.
- Siempre tener fallback a reglas hardcoded si el motor falla.