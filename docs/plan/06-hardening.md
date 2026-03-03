# Fase 6: Hardening (Endurecimiento)

**Agentes involucrados**: `health-monitor-agent`, `software-architecture-agent`, `security-agent`, `observability-agent`

**Objetivo**: Endurecer el sistema para produccion real: chaos engineering, pruebas de carga, penetration testing, compliance GDPR y optimizacion de rendimiento final.

**Prerequisitos**: Fases 4 y 5 completadas.

---

## 6.1 Chaos Engineering

**Agente**: `health-monitor-agent`
**Skills**: `chaos_engineering`, `chaos_toolkit`

### Tareas

- [ ] Instalar Chaos Toolkit: `pip install chaostoolkit chaostoolkit-kubernetes`.

- [ ] Crear directorio `infra/chaos/` con experimentos.

- [ ] Implementar experimentos P0 (criticos):
  - [ ] `liveness-model-unavailable.json` — matar el modelo de liveness, verificar que decision = MANUAL_REVIEW.
  - [ ] `face-match-gpu-exhaustion.json` — saturar GPU, verificar timeout graceful.
  - [ ] `api-gateway-latency.json` — inyectar 5s de latencia, verificar degradacion.

- [ ] Implementar experimentos P1 (importantes):
  - [ ] `redis-down.json` — matar Redis, verificar fallback in-memory para rate limiting.
  - [ ] `postgresql-failover.json` — matar primary, verificar Patroni failover < 30s.
  - [ ] `ocr-timeout.json` — inyectar latencia en OCR, verificar degradacion parcial.
  - [ ] `minio-unavailable.json` — matar MinIO, verificar error controlado.

- [ ] Documentar resultados de cada experimento.

- [ ] Corregir fallos descubiertos y re-ejecutar.

### Checkpoint 6.1
> Resultado esperado: Todos los experimentos de caos P0 pasan. Los P1 tienen acciones correctivas documentadas.

---

## 6.2 Pruebas de Carga

**Agente**: `observability-agent`
**Skills**: `k6`, `locust_load_testing`

### Tareas

- [ ] Crear scripts de load testing con k6 o Locust:
  ```
  Escenario 1: Smoke test — 1 usuario, 1 verificacion
  Escenario 2: Load test — 50 usuarios concurrentes, 5 min
  Escenario 3: Stress test — 200 usuarios concurrentes, 10 min
  Escenario 4: Spike test — 0 → 500 usuarios en 30s
  Escenario 5: Soak test — 50 usuarios, 1 hora
  ```

- [ ] Medir y validar SLOs:
  - p95 latencia < 8 segundos.
  - Error rate < 0.1% bajo carga normal.
  - Throughput minimo: 50 verificaciones/minuto.

- [ ] Identificar cuellos de botella:
  - GPU utilization.
  - PostgreSQL connection pool.
  - Redis memory.
  - Celery queue depth.

- [ ] Optimizar los cuellos de botella encontrados.

- [ ] Re-ejecutar pruebas hasta cumplir SLOs.

### Checkpoint 6.2
> Resultado esperado: El sistema soporta 50 verificaciones concurrentes con p95 < 8s. SLOs cumplidos bajo carga sostenida.

---

## 6.3 Penetration Testing y Security Audit

**Agente**: `security-agent`
**Skills**: `owasp_top10_mitigations`, `bandit_pip_audit`, `trivy_image_scanning`, `waf_modsecurity`

### Tareas

- [ ] Ejecutar OWASP ZAP o Burp Suite contra la API:
  - SQL injection.
  - XSS (en respuestas).
  - CSRF.
  - Authentication bypass.
  - IDOR (Insecure Direct Object Reference).
  - File upload vulnerabilities.

- [ ] Verificar protecciones implementadas:
  - [ ] Rate limiting funciona bajo ataque de fuerza bruta.
  - [ ] JWT no se puede falsificar.
  - [ ] API keys hasheadas, no en texto plano.
  - [ ] Imagenes cifradas en MinIO.
  - [ ] No hay secretos en logs.
  - [ ] No hay PII sin anonimizar en audit logs.

- [ ] Escaneo final de vulnerabilidades:
  - `bandit` — sin findings criticos.
  - `pip-audit` — sin CVEs criticos.
  - `trivy` — imagenes Docker sin vulnerabilidades criticas/altas.

- [ ] Generar informe de seguridad.

### Checkpoint 6.3
> Resultado esperado: 0 vulnerabilidades criticas o altas. Informe de seguridad documentado.

---

## 6.4 Compliance GDPR/LOPD

**Agente**: `security-agent`
**Skills**: `pii_anonymizer_presidio`, `log_retention_policies`, `apscheduler_celery_beat`

### Tareas

- [ ] Verificar politicas de retencion:
  - [ ] Imagenes biometricas se eliminan en < 15 minutos.
  - [ ] Embeddings faciales no se almacenan permanentemente.
  - [ ] Audit logs estan anonimizados (PII enmascarada).
  - [ ] Logs se purgan segun politica de retencion.

- [ ] Implementar endpoint de "derecho al olvido":
  - `DELETE /api/v1/users/{id}/data` — elimina todos los datos asociados.

- [ ] Implementar endpoint de "portabilidad de datos":
  - `GET /api/v1/users/{id}/data` — exporta todos los datos en formato JSON.

- [ ] Documentar el DPA (Data Processing Agreement) template.

- [ ] Documentar el flujo de consentimiento del usuario.

- [ ] Generar informe de compliance GDPR.

### Checkpoint 6.4
> Resultado esperado: Sistema cumple GDPR/LOPD. Datos biometricos se eliminan automaticamente. Derecho al olvido funcional.

---

## 6.5 Optimizacion de Rendimiento

**Agente**: `model-server-agent`, `worker-pool-agent`
**Skills**: `tensorrt`, `fp16_int8_quantization`, `dynamic_batching_triton`, `cuda_streams`

### Tareas

- [ ] Optimizar modelos ML:
  - Quantizar a FP16 los modelos que lo soporten sin perdida significativa.
  - Compilar con TensorRT si hay GPU NVIDIA.
  - Medir impacto en precision (FAR/FRR) tras quantizacion.

- [ ] Optimizar el pipeline del orquestador:
  - Profiling de cada fase para encontrar bottlenecks.
  - Reducir serialización/deserialización innecesaria.
  - Optimizar transferencia de imagenes entre servicios.

- [ ] Optimizar base de datos:
  - Analizar `pg_stat_statements` para queries lentas.
  - Ajustar indices si es necesario.
  - Ajustar pool size de PgBouncer.

- [ ] Optimizar Redis:
  - Analizar key sizes y TTLs.
  - Ajustar max memory y eviction policy.

### Checkpoint 6.5
> Resultado esperado: Tiempo de respuesta total mejorado. Modelos optimizados sin degradacion de precision.

---

## 6.6 Fitness Functions y Monitoring Continuo

**Agente**: `software-architecture-agent`
**Skills**: `fitness_functions`, `coupling_cohesion_metrics`, `dependency_graph_analysis`

### Tareas

- [ ] Implementar fitness functions automatizadas:
  ```python
  # test_architecture.py
  def test_response_time_under_8s():
      """Pipeline completo debe responder en < 8s"""
      ...

  def test_far_below_threshold():
      """FAR debe ser < 0.1%"""
      ...

  def test_no_circular_dependencies():
      """No hay dependencias circulares entre modulos"""
      ...

  def test_coupling_metrics():
      """Acoplamiento entre modulos < umbral"""
      ...
  ```

- [ ] Integrar fitness functions en CI/CD como gate obligatorio.

- [ ] Configurar SLO tracking en Grafana:
  - Error budget dashboard.
  - Burn rate alerts.

- [ ] Documentar runbooks para los incidentes mas comunes:
  - [ ] PostgreSQL failover.
  - [ ] Redis caido.
  - [ ] GPU saturada.
  - [ ] Model server no responde.
  - [ ] Rate limit alcanzado.

### Checkpoint 6.6
> Resultado esperado: Fitness functions pasan en CI/CD. SLO tracking operativo. Runbooks documentados.

---

## 6.7 Documentacion Final

**Agente**: `software-architecture-agent`

### Tareas

- [ ] Documentar la API con OpenAPI/Swagger (auto-generado por FastAPI).

- [ ] Documentar la arquitectura final con diagramas C4 actualizados.

- [ ] Actualizar todos los ADRs con el estado final.

- [ ] Crear guia de operaciones:
  - Despliegue.
  - Escalado.
  - Backup/Restore.
  - Troubleshooting.

- [ ] Crear guia de desarrollo para nuevos contribuidores.

### Checkpoint 6.7
> Resultado esperado: Documentacion completa y actualizada. Cualquier ingeniero nuevo puede entender y contribuir al proyecto.

---

## Criterios de Completitud de Fase 6

- [ ] Experimentos de caos P0 pasan sin fallos
- [ ] SLOs cumplidos bajo pruebas de carga (50 usuarios concurrentes, p95 < 8s)
- [ ] 0 vulnerabilidades criticas/altas en security scan
- [ ] Compliance GDPR verificado (retencion, anonimizacion, derecho al olvido)
- [ ] Modelos optimizados (FP16/TensorRT) sin degradacion de precision
- [ ] Fitness functions en CI/CD
- [ ] Runbooks documentados
- [ ] Documentacion completa

---

## Criterios de Go-Live

Antes de ir a produccion, todos estos criterios deben cumplirse:

- [ ] Todas las fases (1-6) completadas
- [ ] FAR < 0.1% medido sobre dataset de test representativo
- [ ] FRR < 5% medido sobre dataset de test representativo
- [ ] Tasa de deteccion de spoofing > 99%
- [ ] p95 latencia < 8 segundos bajo carga de produccion esperada
- [ ] Disponibilidad > 99.9% medida durante soak test de 24h
- [ ] 0 vulnerabilidades criticas en el ultimo security scan
- [ ] GDPR compliance verificado
- [ ] Backups probados y restauracion validada
- [ ] Runbooks completos y probados
- [ ] Monitoring y alerting operativos
- [ ] Equipo formado en operaciones del sistema
