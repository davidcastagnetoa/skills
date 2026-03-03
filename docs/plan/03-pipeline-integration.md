# Fase 3: Pipeline Integration

**Agentes involucrados**: `orchestrator-agent`, `capture-agent`, `antifraud-agent`, `decision-agent`, `audit-agent`, `worker-pool-agent`

**Objetivo**: Integrar los modulos individuales de Fase 2 en un pipeline completo orquestado, agregar logica antifraude transversal, motor de decision, auditoria y validacion de captura.

**Prerequisitos**: Fase 1 + Fase 2 completadas.

---

## 3.1 Validacion de Captura

**Agente**: `capture-agent`
**Skills**: `virtual_camera_detection`, `laplacian_variance`, `histogram_analysis`, `mediapipe_face_detection`, `input_size_validation`

### Tareas

- [ ] Implementar `ImageQualityValidator`:
  ```python
  class ImageQualityValidator:
      async def validate(self, image: bytes) -> QualityResult:
          sharpness = laplacian_variance(image)      # > 100 = nítido
          brightness = histogram_mean(image)          # 40-220 rango aceptable
          resolution = get_resolution(image)          # min 640x480
          has_face = detect_single_face(image)        # exactamente 1 rostro
          return QualityResult(
              is_valid=all([sharpness, brightness, resolution, has_face]),
              quality_score=weighted_score(...),
              issues=collect_issues(...),
          )
  ```

- [ ] Implementar `VirtualCameraDetector`:
  - Analizar metadatos del stream de video.
  - Detectar drivers conocidos: OBS Virtual Camera, ManyCam, Snap Camera.
  - Verificar coherencia de framerate y resolucion.

- [ ] Implementar `GalleryBlocker`:
  - Verificar que la imagen se capturo en vivo (no subida desde archivo).
  - Analizar EXIF: timestamp, modelo de camara, software.
  - Rechazar imagenes con timestamps antiguos.

- [ ] Implementar validacion de tamano maximo de payload (imagenes > 10MB rechazadas).

- [ ] Tests con imagenes de buena/mala calidad, imagenes de galeria, capturas de camara virtual.

### Checkpoint 3.1
> Resultado esperado: Imagenes borrosas, oscuras, sin rostro o de camara virtual son rechazadas con mensaje descriptivo.

---

## 3.2 Modulo Antifraude

**Agente**: `antifraud-agent`
**Skills**: `blacklist_db`, `device_fingerprinting`, `geoip2_maxmind`, `vpn_proxy_tor_detection`, `isolation_forest`, `dex_mivolo_age_estimator`, `document_expiry_validator`, `redis_rate_limiter`

### Tareas

- [ ] Implementar `DocumentBlacklistChecker`:
  - Consultar tabla `blacklisted_documents` (cacheada en Redis, TTL 5 min).
  - Match por numero de documento.
  - Resultado: blacklisted (hard reject) o clean.

- [ ] Implementar `MultiAttemptDetector`:
  - Detectar multiples intentos desde mismo device_fingerprint en ventana de tiempo.
  - Detectar multiples documentos diferentes desde misma IP.
  - Umbrales configurables: max 3 intentos / hora / dispositivo.

- [ ] Implementar `GeoLocationChecker`:
  - GeoIP2 MaxMind para localizar IP del usuario.
  - Comparar pais de IP con nacionalidad del documento.
  - Flag auxiliar (no bloqueante) si hay discrepancia.

- [ ] Implementar `VPNProxyDetector`:
  - Detectar IPs de VPN/proxy/Tor conocidos.
  - Flag de riesgo (no bloqueante, aumenta fraud_score).

- [ ] Implementar `AgeConsistencyChecker`:
  - Estimar edad visual del rostro de la selfie (DEX o MiVOLO).
  - Comparar con fecha de nacimiento del documento.
  - Tolerancia: +/- 10 anos.
  - Flag si la discrepancia es > 15 anos.

- [ ] Implementar `SessionAnomalyDetector`:
  - Isolation Forest para detectar patrones de sesion inusuales.
  - Features: tiempo entre pasos, numero de reintentos, dispositivo, geolocalizacion.

- [ ] Crear `AntifraudService`:
  ```python
  class AntifraudService:
      async def analyze(self, session: Session, module_results: dict) -> AntifraudResult:
          blacklist = await self.blacklist_checker.check(session.doc_number)
          attempts = await self.multi_attempt.check(session.device_fp, session.ip)
          geo = await self.geo_checker.check(session.ip, session.nationality)
          vpn = await self.vpn_detector.check(session.ip)
          age = await self.age_checker.check(session.selfie, session.dob)
          anomaly = await self.anomaly_detector.score(session)

          risk_flags = collect_flags(blacklist, attempts, geo, vpn, age, anomaly)
          fraud_score = calculate_fraud_score(risk_flags)

          return AntifraudResult(
              fraud_score=fraud_score,
              risk_flags=risk_flags,
              recommended_action=determine_action(fraud_score, risk_flags),
          )
  ```

- [ ] Tests con escenarios de fraude simulados (cada caso de uso del punto 8 del CLAUDE.md).

### Checkpoint 3.2
> Resultado esperado: Los 10 escenarios de fraude del CLAUDE.md son detectados correctamente. Documentos en blacklist se rechazan inmediatamente.

---

## 3.3 Motor de Decision

**Agente**: `decision-agent`
**Skills**: `weighted_score_aggregator`, `hard_rule_engine`, `rule_engine`, `configurable_thresholds`, `decision_explainer`, `human_review_queue`

### Tareas

- [ ] Implementar `HardRuleEngine` — reglas de rechazo/aprobacion inmediata:
  ```python
  HARD_REJECT_RULES = [
      ("liveness_score < 0.3", "Liveness check failed critically"),
      ("face_match_score < 0.5", "Face match below minimum threshold"),
      ("document_expired == True", "Document is expired"),
      ("document_blacklisted == True", "Document is blacklisted"),
      ("no_face_detected == True", "No face detected in selfie"),
  ]
  ```

- [ ] Implementar `WeightedScoreAggregator`:
  ```python
  DEFAULT_WEIGHTS = {
      "liveness_score": 0.25,
      "face_match_score": 0.30,
      "document_forgery_score": 0.20,  # invertido: 1 - forgery
      "ocr_consistency_score": 0.10,
      "antifraud_score": 0.15,          # invertido: 1 - fraud
  }
  ```
  - Pesos almacenados en Redis, modificables sin redeploy.
  - Score global = suma ponderada normalizada.

- [ ] Implementar `DecisionClassifier`:
  ```
  Score >= 0.85          → VERIFIED
  Score 0.60 - 0.85      → MANUAL_REVIEW
  Score < 0.60           → REJECTED
  Hard rule triggered    → REJECTED (bypass score)
  ```

- [ ] Implementar `DecisionExplainer` — razones legibles:
  - Generar lista de razones en lenguaje humano.
  - Indicar que modulos contribuyeron positiva y negativamente.

- [ ] Implementar `ManualReviewQueue`:
  - Encolar sesiones ambiguas para revision humana.
  - Almacenar en PostgreSQL con estado `pending_review`.
  - Endpoint para que reviewers consulten y resuelvan.

- [ ] Crear `DecisionService`:
  ```python
  class DecisionService:
      async def decide(self, session_id: UUID, module_scores: dict) -> DecisionResult:
          # 1. Hard rules
          hard_result = self.hard_rules.evaluate(module_scores)
          if hard_result.triggered:
              return DecisionResult(status="REJECTED", reasons=hard_result.reasons)

          # 2. Weighted score
          global_score = self.aggregator.calculate(module_scores)

          # 3. Classify
          status = self.classifier.classify(global_score)

          # 4. Explain
          reasons = self.explainer.explain(module_scores, global_score, status)

          # 5. Queue for review if needed
          if status == "MANUAL_REVIEW":
              await self.review_queue.enqueue(session_id, module_scores, reasons)

          return DecisionResult(
              status=status,
              confidence_score=global_score,
              reasons=reasons,
          )
  ```

- [ ] Tests con combinaciones de scores que produzcan cada tipo de decision.

### Checkpoint 3.3
> Resultado esperado: Hard rules rechazan correctamente. Scores ponderados clasifican en 3 categorias. Pesos se pueden modificar via Redis sin redeploy. Cola de revision manual funciona.

---

## 3.4 Modulo de Auditoria

**Agente**: `audit-agent`
**Skills**: `structlog`, `hmac_sha256_session_hashing`, `pii_anonymizer_presidio`, `prometheus_client_audit`, `log_retention_policies`, `uuid_v4`, `apscheduler_celery_beat`

### Tareas

- [ ] Implementar `AuditLogger`:
  - Registrar eventos con structlog en formato JSON.
  - Campos obligatorios: session_id, trace_id, event_type, timestamp_us, data.
  - Escribir en tabla `audit_logs` de PostgreSQL.

- [ ] Implementar `PIIAnonymizer`:
  - Detectar y enmascarar PII con Microsoft Presidio.
  - Campos a anonimizar: nombre, numero de documento, fecha nacimiento.
  - Formato de anonimizacion: `"Juan Perez" → "J*** P***"`.

- [ ] Implementar `SessionHasher`:
  - HMAC-SHA256 por sesion para garantizar integridad.
  - Hash calculado sobre todos los eventos de la sesion.
  - Almacenar hash final en `audit_logs`.

- [ ] Implementar `DataRetentionManager`:
  - Job de Celery Beat que cada 5 minutos:
    - Elimina imagenes de MinIO con > 15 min de antiguedad.
    - Elimina embeddings faciales temporales de Redis.
  - Job diario que purga audit_logs segun politica de retencion.

- [ ] Implementar metricas de auditoria:
  - FAR (False Acceptance Rate) — tasa de impostores aceptados.
  - FRR (False Rejection Rate) — tasa de legitimos rechazados.
  - Tiempo medio de procesamiento por modulo.
  - Distribucion de decisiones (VERIFIED/REJECTED/MANUAL_REVIEW).

### Checkpoint 3.4
> Resultado esperado: Cada sesion de verificacion genera un trail de auditoria completo, anonimizado, con hash de integridad. Datos biometricos se purgan tras 15 min.

---

## 3.5 Orquestador del Pipeline

**Agente**: `orchestrator-agent`
**Skills**: `celery_canvas`, `asyncio_patterns`, `timeout_manager`, `graceful_degradation`

### Tareas

- [ ] Implementar `PipelineOrchestrator` — flujo completo:
  ```python
  class PipelineOrchestrator:
      async def run(self, request: VerificationRequest) -> VerificationResponse:
          session = await self.create_session(request)
          try:
              # Fase 0: Validacion de captura
              capture_result = await self.capture_validator.validate(
                  request.selfie_image, request.document_image
              )
              if not capture_result.is_valid:
                  return self.reject(session, capture_result.issues)

              # Guardar imagenes en MinIO
              await self.storage.upload_session_images(session.id, request)

              # Fase 1: Paralela — liveness + doc_processing
              liveness_task = self.run_liveness(session.id, request.selfie_frames)
              doc_task = self.run_doc_processing(session.id, request.document_image)
              liveness_result, doc_result = await asyncio.gather(
                  liveness_task, doc_task, return_exceptions=True
              )

              # Fase 2: Paralela — face_match + OCR
              face_task = self.run_face_match(session.id, request.selfie_image, doc_result.face_region)
              ocr_task = self.run_ocr(session.id, doc_result.processed_image)
              face_result, ocr_result = await asyncio.gather(
                  face_task, ocr_task, return_exceptions=True
              )

              # Fase 3: Secuencial — antifraude
              antifraud_result = await self.run_antifraud(session, {
                  "liveness": liveness_result,
                  "face_match": face_result,
                  "doc_processing": doc_result,
                  "ocr": ocr_result,
              })

              # Fase 4: Secuencial — decision
              decision = await self.run_decision(session, {
                  "liveness_score": liveness_result.liveness_score,
                  "face_match_score": face_result.similarity_score,
                  "document_forgery_score": doc_result.forgery_score,
                  "ocr_consistency_score": ocr_result.data_consistency_score,
                  "antifraud_score": antifraud_result.fraud_score,
              })

              # Registrar resultado
              await self.save_result(session, decision)
              await self.audit.log_session_complete(session, decision)

              return self.build_response(session, decision)

          except asyncio.TimeoutError:
              return self.timeout_response(session)
          except Exception as e:
              await self.audit.log_error(session, e)
              return self.error_response(session, e)
  ```

- [ ] Implementar manejo de errores parciales:
  - Si liveness falla → MANUAL_REVIEW (critico pero no fatal).
  - Si OCR falla → continuar con penalizacion de score.
  - Si doc_processing falla → REJECTED.
  - Si face_match falla → MANUAL_REVIEW.

- [ ] Implementar timeout global del pipeline (8 segundos).

- [ ] Implementar progreso de sesion en Redis:
  ```json
  {
    "session_id": "uuid",
    "current_phase": "face_match",
    "phases_completed": ["capture_validation", "liveness", "doc_processing"],
    "started_at": "timestamp",
    "elapsed_ms": 3200
  }
  ```

- [ ] Conectar con el endpoint `POST /api/v1/verify`:
  - Recibir request.
  - Ejecutar pipeline via orquestador.
  - Retornar respuesta.

- [ ] Implementar `GET /api/v1/verify/{id}` para consultar progreso/resultado.

- [ ] Test end-to-end completo: enviar selfie + documento → recibir decision.

### Checkpoint 3.5
> Resultado esperado: El pipeline completo funciona end-to-end. Una solicitud de verificacion pasa por todos los modulos y retorna VERIFIED, REJECTED o MANUAL_REVIEW en < 8 segundos.

---

## Criterios de Completitud de Fase 3

- [ ] Pipeline end-to-end funcional (selfie + documento → decision)
- [ ] Paralelismo de fases reduce el tiempo total vs secuencial
- [ ] Manejo de errores parciales funciona (degradacion graceful)
- [ ] 10 escenarios de fraude del CLAUDE.md son detectados
- [ ] Motor de decision clasifica correctamente con pesos configurables
- [ ] Auditoria completa: trail anonimizado con hash de integridad
- [ ] Datos biometricos se purgan automaticamente tras 15 min
- [ ] Timeout global de 8s se respeta
- [ ] Tests e2e pasan con multiples escenarios (positivos, negativos, edge cases)
- [ ] Metricas FAR/FRR se pueden calcular a partir de los audit logs
