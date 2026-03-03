---
name: chaos_engineering
description: Disciplina de ingeniería del caos para validar resiliencia del pipeline KYC mediante experimentos controlados
type: Practice
priority: Importante
mode: Self-hosted
---

# chaos_engineering

Disciplina y metodología de ingeniería del caos aplicada al sistema de verificación de identidad KYC. Define los principios, procesos y estrategias para diseñar y ejecutar experimentos de caos que validen la resiliencia de cada módulo del pipeline (liveness, OCR, face_match, antifraud, decision engine). A diferencia de `chaos_toolkit` (que es la herramienta de ejecución), esta skill cubre la planificación, el diseño experimental, la priorización de hipótesis y la cultura de resiliencia.

## When to use

Usar cuando se necesite diseñar la estrategia de resiliencia del sistema KYC, definir hipótesis de fallo, priorizar experimentos y establecer el proceso de game days. Aplicar antes de configurar herramientas concretas como Chaos Toolkit o LitmusChaos. Pertenece al **health_monitor_agent** y se usa en las fases de planificación de resiliencia y antes de releases críticos.

## Instructions

1. Definir la matriz de hipótesis de fallo para el pipeline KYC:
```
┌──────────────────────┬────────────────────────┬──────────────┬─────────────┐
│ Componente           │ Hipótesis de fallo     │ Impacto      │ Prioridad   │
├──────────────────────┼────────────────────────┼──────────────┼─────────────┤
│ Liveness Detection   │ Modelo ML no responde  │ Crítico      │ P0          │
│ Face Match (ArcFace) │ GPU saturada/timeout   │ Crítico      │ P0          │
│ OCR (PaddleOCR)      │ Servicio caído         │ Alto         │ P1          │
│ Redis (rate limiter) │ Nodo Redis caído       │ Alto         │ P1          │
│ PostgreSQL           │ Failover de Patroni    │ Alto         │ P1          │
│ MinIO                │ Storage no disponible  │ Medio        │ P2          │
│ API Gateway          │ Latencia extrema       │ Crítico      │ P0          │
│ Decision Engine      │ Módulo parcial offline │ Alto         │ P1          │
└──────────────────────┴────────────────────────┴──────────────┴─────────────┘
```

2. Establecer el proceso de diseño de experimentos:
```
[Definir estado estable]
       ↓
[Formular hipótesis: "Si X falla, el sistema debe Y"]
       ↓
[Diseñar experimento con blast radius mínimo]
       ↓
[Ejecutar en staging con monitorización activa]
       ↓
[Analizar resultados vs. hipótesis]
       ↓
[Documentar hallazgos y acciones correctivas]
       ↓
[Implementar mejoras de resiliencia]
       ↓
[Re-ejecutar para validar corrección]
```

3. Definir el estado estable del pipeline KYC:
```yaml
steady_state:
  api_gateway:
    - response_time_p99 < 8s
    - error_rate < 0.1%
    - availability > 99.9%
  liveness_module:
    - detection_rate > 99%
    - response_time < 2s
  face_match_module:
    - FAR < 0.1%
    - FRR < 5%
    - response_time < 3s
  ocr_module:
    - extraction_accuracy > 95%
    - response_time < 2s
  decision_engine:
    - always returns a decision (VERIFIED/REJECTED/MANUAL_REVIEW)
    - never approves without liveness + face_match
```

4. Catálogo de experimentos priorizados para el sistema KYC:
```yaml
experiments:
  P0_critical:
    - name: "liveness-model-unavailable"
      hypothesis: "Si el modelo de liveness cae, el sistema debe rechazar con MANUAL_REVIEW, nunca aprobar"
      method: "Detener el contenedor del servicio de liveness"
      expected: "Decision engine emite MANUAL_REVIEW con reason 'liveness_unavailable'"

    - name: "face-match-gpu-exhaustion"
      hypothesis: "Si la GPU está saturada, las peticiones deben hacer queue con timeout, no crashear"
      method: "Saturar GPU con peticiones concurrentes (10x normal)"
      expected: "Timeout graceful tras 8s, respuesta de error controlada"

    - name: "api-gateway-latency-spike"
      hypothesis: "Si la latencia del gateway sube a 5s, el cliente recibe feedback de espera"
      method: "Inyectar latencia de 5s con tc netem"
      expected: "Cliente muestra indicador de carga, no timeout abrupto"

  P1_high:
    - name: "redis-rate-limiter-down"
      hypothesis: "Sin Redis, el rate limiting debe degradar a in-memory con límites conservadores"
      method: "Detener Redis"
      expected: "Rate limiting funciona con fallback local"

    - name: "postgresql-failover"
      hypothesis: "Durante un failover de Patroni, las escrituras se pausan <5s y se reanudan sin pérdida"
      method: "Kill del nodo primario de PostgreSQL"
      expected: "Patroni promueve réplica, aplicación reconecta automáticamente"

    - name: "ocr-service-timeout"
      hypothesis: "Si OCR tarda >5s, el pipeline marca el módulo como degradado y continúa"
      method: "Inyectar latencia de 10s al servicio OCR"
      expected: "Decision engine reporta ocr_degraded, resultado parcial disponible"
```

5. Planificar Game Days trimestrales:
```yaml
game_day_checklist:
  preparation:
    - Notificar al equipo con 48h de antelación
    - Verificar que staging replica la topología de producción
    - Confirmar que monitorización (Prometheus/Grafana) está activa
    - Preparar runbook de rollback para cada experimento
    - Designar un facilitador y un observador de métricas

  execution:
    - Ejecutar experimentos en orden de prioridad (P0 → P1 → P2)
    - Máximo 3 experimentos por sesión
    - Pausa de 10 minutos entre experimentos para verificar estado estable
    - Documentar observaciones en tiempo real

  post_mortem:
    - Comparar resultados vs. hipótesis
    - Clasificar hallazgos: OK / Degradación aceptable / Fallo crítico
    - Crear tickets para fallos encontrados con prioridad y owner
    - Actualizar la matriz de hipótesis con los resultados
```

6. Métricas de madurez de resiliencia:
```yaml
resilience_maturity:
  level_1_basic:
    - Health checks implementados en todos los servicios
    - Timeouts configurados en todas las llamadas inter-servicio
    - Al menos 1 experimento de caos ejecutado en staging

  level_2_intermediate:
    - Circuit breakers en todas las dependencias externas
    - Fallbacks definidos para todos los módulos del pipeline
    - Game Days trimestrales con al menos 5 experimentos
    - Runbooks actualizados para los 3 escenarios de fallo más comunes

  level_3_advanced:
    - Experimentos de caos en producción (canary, con blast radius limitado)
    - Inyección de fallos automatizada en CI/CD (pre-release gate)
    - Cobertura de resiliencia >80% de los componentes críticos
    - Métricas de MTTR (Mean Time To Recovery) <5 minutos
```

## Notes

- Esta skill define la estrategia y el proceso; para la ejecución técnica de los experimentos, usar la skill `chaos_toolkit`.
- Nunca ejecutar experimentos de caos en producción sin haber validado primero en staging y sin aprobación explícita del equipo.
- Comenzar por los experimentos P0 (módulos críticos del pipeline: liveness y face_match) antes de avanzar a otros componentes.
- Documentar cada experimento como un ADR usando la skill `adr_tools` para mantener un registro histórico de decisiones de resiliencia.
- La regla de oro: si el sistema falla un experimento, eso es un éxito del proceso de chaos engineering porque se descubrió una debilidad antes de que afectara a usuarios reales.
