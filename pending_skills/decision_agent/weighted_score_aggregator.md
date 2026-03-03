---
name: weighted_score_aggregator
description: Combinar scores de todos los agentes con pesos configurables por entorno
type: Algorithm
priority: Esencial
mode: Self-hosted
---

# weighted_score_aggregator

Algoritmo de agregación ponderada que combina los scores parciales de cada agente del pipeline en un score global de verificación. Los pesos son configurables por entorno sin necesidad de redeploy.

## When to use

Usar en el `decision_agent` como paso final antes de aplicar las hard rules. Recibe los scores de liveness, face_match, document_forgery, ocr_consistency y fraud_analysis.

## Instructions

1. Definir pesos por defecto en config:
   ```python
   WEIGHTS = {
       'liveness_score': 0.25,
       'face_match_score': 0.30,
       'document_forgery_score': 0.20,
       'ocr_consistency_score': 0.10,
       'fraud_score': 0.15,
   }
   ```
2. Cargar pesos desde Redis (configurables sin redeploy): `weights = redis.hgetall('config:weights')`.
3. Calcular score global: `global_score = sum(score * weight for score, weight in zip(scores, weights))`.
4. Verificar que los pesos suman 1.0: `assert abs(sum(weights.values()) - 1.0) < 0.001`.
5. Clasificar: `VERIFIED` si score > 0.85, `REJECTED` si < 0.50, `MANUAL_REVIEW` en medio.
6. Registrar scores individuales y global en auditoría.

## Notes

- Los pesos deben ser ajustados empíricamente tras analizar FAR/FRR en el dataset de validación.
- Implementar versioning de configuración de pesos para poder hacer rollback.
- El score global es la base, pero las hard rules pueden overridear la decisión.
