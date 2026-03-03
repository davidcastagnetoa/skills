# Agents.md — Agentes del Proyecto de Verificación de Identidad

## Filosofía de Diseño de Agentes

Cada agente tiene una **responsabilidad única y bien delimitada** (principio de responsabilidad única). Los agentes se comunican a través de una **cola de mensajes / pipeline de datos** orquestado por el Agente Orquestador. Esta arquitectura permite reemplazar o mejorar cada agente de forma independiente sin afectar al resto.

El sistema se divide en tres capas:

- **Capa de Arquitectura**: un único agente transversal que define, gobierna y hace evolucionar la estructura del sistema completo. Actúa antes y durante el desarrollo, no en tiempo de ejecución.
- **Capa de Negocio / KYC**: agentes que ejecutan la lógica de verificación de identidad.
- **Capa de Infraestructura Backend**: agentes que garantizan que el sistema sea rápido, robusto, seguro y observable en producción.

Las tres capas son igual de importantes. Un sistema KYC preciso pero con arquitectura incoherente se convierte en deuda técnica que impide evolucionar. Un sistema bien arquitectado pero lento o inseguro no es apto para producción.

---

## Mapa Completo de Agentes

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                        CAPA DE ARQUITECTURA                               ║
║                                                                           ║
║         ┌─────────────────────────────────────────────────────┐          ║
║         │            AGENTE DE ARQUITECTURA DE SOFTWARE        │          ║
║         │  (define contratos, ADRs, estándares y evolución     │          ║
║         │   del sistema — opera en diseño, no en runtime)      │          ║
║         └──────────────────────────┬──────────────────────────┘          ║
╚══════════════════════════════════╤═╧══════════════════════════════════════╝
                                   │ gobierna
╔══════════════════════════════════╧════════════════════════════════════════╗
║                     CAPA DE INFRAESTRUCTURA BACKEND                       ║
║                                                                           ║
║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ║
║  │ API GATEWAY  │  │    CACHE     │  │    HEALTH    │  │  SECURITY   │  ║
║  │    AGENT     │  │    AGENT     │  │   MONITOR    │  │   AGENT     │  ║
║  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘  ║
║         │                 │                  │                 │         ║
║  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────────┐  ║
║  │  DATABASE    │  │OBSERVABILITY │  │         MODEL SERVER          │  ║
║  │    AGENT     │  │    AGENT     │  │            AGENT              │  ║
║  └──────┬───────┘  └──────────────┘  └──────────────┬──────────────┘  ║
║         │                                            │                  ║
╚═════════╪════════════════════════════════════════════╪══════════════════╝
          │                                            │
╔═════════╪════════════════════════════════════════════╪══════════════════╗
║         ▼            CAPA DE NEGOCIO / KYC           ▼                  ║
║                                                                          ║
║                      ┌─────────────────────┐                            ║
║                      │  AGENTE ORQUESTADOR  │                            ║
║                      └──────────┬──────────┘                            ║
║           ┌──────────────────────┼──────────────────────┐               ║
║           │                      │                      │               ║
║   ┌───────────────┐      ┌───────────────┐      ┌───────────────┐       ║
║   │   CAPTURA     │      │   DOCUMENTO   │      │   DECISIÓN    │       ║
║   └───────┬───────┘      └───────┬───────┘      └───────┬───────┘       ║
║           │                      │                      │               ║
║   ┌───────────────┐      ┌───────────────┐              │               ║
║   │   LIVENESS    │      │      OCR      │              │               ║
║   └───────┬───────┘      └───────┬───────┘              │               ║
║           │                      │                      │               ║
║   ┌───────────────┐      ┌───────────────┐              │               ║
║   │  FACE MATCH   │◄─────┤   ANTIFRAUDE  ├──────────────┘               ║
║   └───────────────┘      └───────────────┘                              ║
║                                                                          ║
║          ┌─────────────────────────────────────────────────┐            ║
║          │              WORKER POOL AGENT                  │            ║
║          │  (gestiona la ejecución de todos los agentes    │            ║
║          │   computacionalmente intensivos de esta capa)   │            ║
║          └─────────────────────────────────────────────────┘            ║
║                                                                          ║
║          ┌─────────────────────────────────────────────────┐            ║
║          │                AUDITORÍA AGENT                  │            ║
║          └─────────────────────────────────────────────────┘            ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

# CAPA DE ARQUITECTURA

---

## 0. Agente de Arquitectura de Software (`software_architecture_agent`)

**Rol**: Responsable de definir, documentar, gobernar y hacer evolucionar la arquitectura del sistema completo. Es el único agente que opera **en tiempo de diseño y desarrollo**, no en tiempo de ejecución. Su output no es código que se ejecuta, sino decisiones, contratos y estándares que guían a todos los demás agentes.

Sin este agente, cada agente técnico puede crecer en direcciones distintas, los contratos entre servicios se vuelven implícitos, y el sistema acumula deuda técnica hasta ser imposible de mantener o escalar.

**Responsabilidades**:

### Diseño y documentación de la arquitectura

- Definir y mantener actualizado el **diagrama de arquitectura del sistema** completo (C4 Model: Context → Containers → Components → Code).
- Establecer los **patrones arquitectónicos** adoptados por el proyecto y los criterios que justifican su elección:
  - Comunicación entre servicios: cuándo usar REST, gRPC, mensajería asíncrona (Celery/Redis).
  - Patrones de resiliencia: circuit breaker, retry, bulkhead, timeout.
  - Patrones de datos: event sourcing para auditoría, CQRS si aplica, cache-aside pattern.
- Definir la **topología de despliegue**: distribución de servicios en nodos, afinidad GPU, zonas de disponibilidad.
- Documentar las **dependencias entre agentes** y garantizar que el grafo de dependencias no tiene ciclos.
- Mantener el **glosario técnico** del proyecto: términos, acrónimos y conceptos compartidos por todos los agentes.

### Architecture Decision Records (ADRs)

- Registrar cada decisión arquitectónica relevante en formato ADR estandarizado:
  - **Contexto**: qué problema se estaba resolviendo.
  - **Opciones evaluadas**: qué alternativas se consideraron.
  - **Decisión**: qué se eligió y por qué.
  - **Consecuencias**: trade-offs aceptados (rendimiento vs. complejidad, consistencia vs. disponibilidad, etc.).
  - **Estado**: `proposed` → `accepted` → `deprecated` → `superseded`.
- Ejemplos de ADRs que este agente debe generar para el proyecto:
  - ADR-001: Elección de FastAPI sobre Flask/Django (async nativo, rendimiento, tipado).
  - ADR-002: Celery + Redis vs. Kafka como broker de mensajería (simplicidad vs. durabilidad).
  - ADR-003: InsightFace/ArcFace vs. DeepFace como modelo de face match (precisión vs. flexibilidad).
  - ADR-004: NVIDIA Triton vs. TorchServe para model serving (GPU optimization vs. facilidad de uso).
  - ADR-005: Redis Sentinel vs. Redis Cluster para alta disponibilidad del caché.
  - ADR-006: MinIO vs. S3 como object storage (self-hosted vs. managed).
  - ADR-007: PostgreSQL con Patroni vs. CockroachDB para la BBDD principal.
  - ADR-008: Estrategia de liveness: pasivo + activo combinados vs. solo activo.
  - ADR-009: mTLS interno con Istio vs. Linkerd (funcionalidad vs. complejidad).
  - ADR-010: Grafana Loki vs. ELK Stack para logs centralizados.

### Definición de contratos entre agentes (API Contracts)

- Definir y versionar los **contratos de interfaz** entre todos los agentes del sistema:
  - Schemas de los mensajes en las colas Celery (qué campos, qué tipos, qué validaciones).
  - Schemas de las respuestas REST/gRPC entre servicios.
  - Contratos de los eventos de auditoría que emite cada agente.
- Garantizar que los contratos son **backwards-compatible** al evolucionar (versionado semántico).
- Mantener un **schema registry** centralizado (Pydantic models o AsyncAPI spec) como fuente única de verdad de todos los contratos.
- Detectar y prevenir **breaking changes** entre versiones: si un agente cambia su interfaz, este agente valida que los consumidores no se rompen.

### Estándares de código y calidad técnica

- Definir y publicar las **guías de estilo de código** del proyecto (Python: Black + Ruff + mypy, tipo hints obligatorios).
- Establecer los **estándares de testing** por capa:
  - Unitarios: cobertura mínima del 80% por módulo de negocio.
  - Integración: smoke tests de cada agente con sus dependencias reales.
  - End-to-end: flujos completos de verificación (positivos, negativos y ataques simulados).
  - Performance: pruebas de carga para validar los SLOs (< 8s p95) antes de cada release.
- Definir la **estrategia de gestión de dependencias**: pinning de versiones, política de actualizaciones de seguridad, escaneo de vulnerabilidades (Dependabot, Safety).
- Establecer las **reglas de CI/CD**: qué gates debe superar cada PR antes de hacer merge (tests, linting, type checking, security scan, schema compatibility check).

### Gestión de la deuda técnica

- Mantener un **backlog de deuda técnica** priorizado: qué hay que refactorizar, cuándo y por qué.
- Definir el umbral de deuda técnica aceptable por sprint.
- Detectar **code smells** estructurales: acoplamiento excesivo entre agentes, violaciones del principio de responsabilidad única, lógica de negocio filtrada a la capa de infraestructura.
- Planificar la **estrategia de migración** cuando una tecnología del stack necesita ser reemplazada (ej.: si un modelo ML queda obsoleto o un servicio deja de mantenerse).

### Evolución y planificación técnica

- Definir el **roadmap técnico** del sistema: qué mejoras de arquitectura se planifican en cada fase del proyecto.
- Evaluar proactivamente el impacto de nuevas tecnologías relevantes (nuevos modelos de liveness, nuevas versiones de Triton, etc.).
- Realizar **fitness functions** periódicas: pruebas automatizadas que verifican que el sistema sigue cumpliendo sus requisitos arquitectónicos (latencia, acoplamiento, disponibilidad).
- Gestionar la **estrategia de escalabilidad horizontal**: definir qué agentes pueden escalar stateless y cuáles requieren coordinación de estado.

**Entradas**: Requisitos funcionales y no funcionales del sistema, feedback de los demás agentes sobre fricciones técnicas, incidentes de producción, nuevas tecnologías a evaluar.

**Salidas**:

- Diagramas de arquitectura vivos (C4 Model).
- Repositorio de ADRs.
- Schema registry de contratos entre agentes.
- Guías de estilo y estándares técnicos.
- Backlog de deuda técnica.
- Roadmap técnico.
- Fitness functions automatizadas.

**Nota importante**: este agente es el único del sistema que tiene **autoridad para rechazar cambios** que violen los principios arquitectónicos establecidos, independientemente de la urgencia del cambio. Su función incluye el "arquitectura como código": todos los documentos que produce viven en el repositorio de código y se revisan como cualquier otro PR.

---

# CAPA DE NEGOCIO / KYC

---

## 1. Agente Orquestador (`orchestrator_agent`)

**Rol**: Director de la sesión de verificación. Gestiona el ciclo de vida completo desde que el usuario inicia hasta que se emite la decisión final.

**Responsabilidades**:

- Crear y gestionar la sesión de verificación (`session_id` UUID v4).
- Invocar a los agentes KYC en el orden correcto, respetando dependencias del pipeline.
- Ejecutar en **paralelo** los agentes que no tienen dependencia entre sí para minimizar el tiempo total de verificación.
- Agregar los scores parciales de cada agente en un score global ponderado.
- Aplicar reglas de negocio para la decisión final.
- Gestionar timeouts por agente con degradado graceful: si un agente no crítico falla, el pipeline continúa con penalización de score; si uno crítico falla, se retorna error controlado.
- Emitir la respuesta estructurada al cliente vía webhook o polling.

**Estrategia de paralelismo del pipeline**:

```
Fase 1 (paralela):   liveness_agent  ║  document_processor_agent
Fase 2 (paralela):   face_match_agent ║  ocr_agent
Fase 3 (secuencial): antifraud_agent  ← necesita salidas de fases 1 y 2
Fase 4 (secuencial): decision_agent
```

**Entradas**: Solicitud de verificación con `session_id` y metadatos del dispositivo.

**Salidas**: `{ status, confidence_score, reasons[], modules_scores, session_id, timestamp, processing_time_ms }`.

---

## 2. Agente de Captura (`capture_agent`)

**Rol**: Controlar y validar que los medios capturados (selfie y documento) cumplen los requisitos de calidad antes de pasar al pipeline.

**Responsabilidades**:

- Verificar que la selfie proviene de la cámara en vivo (no de galería ni archivo).
- Detectar cámaras virtuales (OBS, ManyCam) mediante fingerprinting de driver.
- Validar calidad de imagen: nitidez (laplaciano), iluminación (histograma), resolución mínima.
- Validar presencia de exactamente un rostro en la selfie.
- Validar legibilidad del documento (bordes detectables, sin reflejos excesivos).
- Proporcionar feedback en tiempo real al usuario si la calidad es insuficiente.

**Entradas**: Stream de video (selfie), imagen del documento.

**Salidas**: Frames validados de selfie, imagen corregida del documento, `{ quality_score, issues[] }`.

---

## 3. Agente de Detección de Vida (`liveness_agent`)

**Rol**: Determinar con la mayor fiabilidad posible que el usuario es una persona real y está presente físicamente frente a la cámara en ese momento.

**Responsabilidades**:

- **Liveness pasivo**: análisis de micro-textura de piel, estimación de profundidad monocular, optical flow.
- **Liveness activo (challenge-response)**: desafíos aleatorios (parpadear, girar la cabeza, sonreír) verificados en tiempo real.
- **Anti-replay**: detectar videos pregrabados reproducidos ante la cámara.
- **Anti-deepfake**: detectar artefactos GAN e inconsistencias de iluminación.
- **Anti-cámara virtual**: verificar coherencia del stream y metadatos del dispositivo.

**Entradas**: Secuencia de frames de video (mínimo 3–5 segundos).

**Salidas**: `{ is_live: bool, liveness_score: float, attack_type_detected: string|null, challenge_passed: bool }`.

---

## 4. Agente de Procesamiento de Documento (`document_processor_agent`)

**Rol**: Procesar la imagen del documento de identidad para extracción de información y análisis de autenticidad.

**Responsabilidades**:

- Detectar y recortar el documento (contour detection, bounding box).
- Corrección de perspectiva (transformación homográfica).
- Mejora de imagen: denoising, sharpening, normalización CLAHE.
- Clasificar el tipo de documento y el país de emisión.
- Detectar manipulación digital: ELA, Copy-Move Forgery, análisis EXIF, consistencia tipográfica.
- Extraer la región de la foto del titular.

**Entradas**: Imagen del documento en bruto.

**Salidas**: Imagen procesada, imagen del rostro del titular, tipo de documento, `{ forgery_score, detected_anomalies[] }`.

---

## 5. Agente OCR (`ocr_agent`)

**Rol**: Extraer la información textual del documento de identidad de forma precisa.

**Responsabilidades**:

- Extraer campos clave: nombre, fecha de nacimiento, número de documento, expiración, nacionalidad.
- Leer y parsear la MRZ (ICAO 9303) con validación de checksums.
- Detectar inconsistencias entre MRZ y campos visuales del documento.
- Normalizar datos extraídos a formato estándar.

**Entradas**: Imagen del documento procesada.

**Salidas**: `{ name, date_of_birth, doc_number, expiry_date, nationality, mrz_valid, mrz_checksum_valid, data_consistency_score }`.

---

## 6. Agente de Comparación Facial (`face_match_agent`)

**Rol**: Determinar si el rostro de la selfie corresponde al rostro de la foto del documento.

**Responsabilidades**:

- Detectar y alinear rostros con landmarks faciales.
- Generar embeddings faciales (ArcFace o equivalente).
- Calcular similitud coseno entre embeddings.
- Gestionar diferencia de calidad entre foto de documento y selfie en vivo.
- Aplicar super-resolución en la foto del documento si es necesario.

**Entradas**: Frame de selfie validado, imagen del rostro del documento.

**Salidas**: `{ match: bool, similarity_score: float, confidence: float }`.

---

## 7. Agente Antifraude (`antifraud_agent`)

**Rol**: Análisis transversal de señales de fraude que no puede detectar ningún agente individual.

**Responsabilidades**:

- Verificar coherencia de edad entre rostro y fecha de nacimiento del documento.
- Comparar número de documento contra lista negra interna.
- Detectar múltiples intentos con documentos distintos desde el mismo dispositivo/IP.
- Verificar geolocalización frente a nacionalidad del documento.
- Detectar VPN/proxy/Tor.
- Rate limiting inteligente por dispositivo/IP/documento.
- Verificar expiración del documento.

**Entradas**: Salidas de todos los agentes KYC + metadatos de la sesión.

**Salidas**: `{ fraud_score: float, risk_flags: string[], recommended_action: 'approve'|'reject'|'manual_review' }`.

---

## 8. Agente de Decisión (`decision_agent`)

**Rol**: Tomar la decisión final de verificación combinando todas las señales del pipeline.

**Responsabilidades**:

- Combinar scores con pesos configurables por módulo.
- Aplicar reglas de rechazo automático (hard rules) independientes del score global.
- Clasificar el resultado: `VERIFIED`, `REJECTED`, `MANUAL_REVIEW`.
- Generar explicación de la decisión legible por humanos.
- Encolar casos para revisión manual cuando el score es ambiguo.

**Entradas**: Scores y flags de todos los agentes.

**Salidas**: `{ status, confidence_score, reasons[], processing_time_ms }`.

---

## 9. Agente de Auditoría (`audit_agent`)

**Rol**: Registrar de forma completa e inmutable todos los eventos del proceso de verificación.

**Responsabilidades**:

- Registrar cada evento con timestamp preciso (µs).
- Anonimizar PII en logs según GDPR.
- Generar hash de integridad (HMAC-SHA256) por sesión para no repudio.
- Gestionar retención y eliminación automática de datos biométricos (máx. 15 min).
- Exponer métricas: FAR, FRR, tiempos de respuesta por agente.

**Entradas**: Eventos de todos los agentes a lo largo de la sesión.

**Salidas**: Log de auditoría cifrado, métricas agregadas, hash de sesión.

---

# CAPA DE INFRAESTRUCTURA BACKEND

Estos agentes no forman parte de la lógica KYC pero son **imprescindibles** para que el sistema sea rápido, robusto y seguro en producción.

---

## 10. Agente API Gateway (`api_gateway_agent`)

**Rol**: Punto de entrada único del sistema. Controla, protege y enruta todo el tráfico antes de que llegue a la capa de negocio.

**Responsabilidades**:

**Seguridad de entrada:**

- Terminación TLS 1.3 — todo el tráfico cifrado en tránsito.
- Autenticación de clientes: JWT (RS256), API Keys, OAuth 2.0 según el tipo de cliente.
- Validación y revocación de tokens (blacklist en Redis).
- Protección DDoS: rate limiting global por IP con sliding window.
- Bloqueo de rangos de IP maliciosas.
- Validación de Content-Type y tamaño máximo de payload (imágenes pesadas).
- Sanitización de inputs — rechazar payloads malformados antes de entrar al pipeline.
- Headers de seguridad HTTP: HSTS, X-Content-Type-Options, X-Frame-Options, CSP.
- CORS configurado por entorno (desarrollo vs. producción).

**Enrutamiento y balanceo:**

- Enrutar peticiones al microservicio correcto según path y versión de API.
- Load balancing entre instancias de workers: round-robin, least-connections o weighted.
- Soporte de múltiples versiones de API simultáneas con deprecation gradual.

**Resiliencia:**

- Circuit breaker por servicio downstream: si falla repetidamente, abrir el circuito y devolver 503 en lugar de dejar peticiones en espera indefinida.
- Retry automático con backoff exponencial para errores transitorios (5xx).
- Timeout global configurable por tipo de endpoint.
- Graceful degradation: si un servicio no crítico no está disponible, devolver respuesta parcial en lugar de error total.

**Observabilidad:**

- Log de cada petición: IP, endpoint, latencia, status code.
- Propagación de `trace_id` a todos los servicios downstream.
- Métricas: RPS, latencia p50/p95/p99, tasa de errores por endpoint.

**Entradas**: Peticiones HTTP/2 desde clientes móviles y web.

**Salidas**: Peticiones autenticadas forwarded al orquestador; respuestas estructuradas al cliente.

**Tecnología recomendada**: **Nginx** con módulo Lua para lógica custom (opción battle-tested, máxima performance), o **Traefik** como alternativa con autodiscovery nativo en Kubernetes.

---

## 11. Agente de Caché (`cache_agent`)

**Rol**: Reducir la latencia y la carga computacional evitando recalcular resultados ya obtenidos recientemente.

**Responsabilidades**:

**Caché de resultados ML:**

- Cachear embeddings faciales de documentos ya procesados (clave: hash de la imagen del documento).
- Cachear resultados de OCR para imágenes idénticas.
- TTL corto (5–15 minutos) para no reutilizar datos entre sesiones distintas.

**Caché de sesión activa:**

- Almacenar el estado de la sesión durante todo el pipeline (evitar I/O a PostgreSQL en cada paso intermedio).
- Acceso O(1) por `session_id`.

**Caché de datos operativos:**

- Lista negra de documentos: actualización periódica desde PostgreSQL, servida desde Redis para acceso en < 1ms.
- Configuración de umbrales y pesos del decision engine.
- Resultados de geolocalización por IP (TTL 1 hora).

**Rate limiting:**

- Contadores deslizantes (sliding window) por IP/dispositivo.
- Listas de IPs bloqueadas temporalmente.

**Alta disponibilidad:**

- Redis Sentinel para HA sin Kubernetes, o Redis Cluster para sharding horizontal.
- Persistencia RDB + AOF para recuperación tras reinicio.
- Réplicas de lectura para distribuir la carga.
- Eviction policy LRU con memoria máxima configurada.

**Entradas**: Solicitudes de lectura/escritura de caché desde todos los agentes.

**Salidas**: Datos cacheados o `MISS`.

---

## 12. Agente de Worker Pool (`worker_pool_agent`)

**Rol**: Gestionar el pool de workers que ejecutan las tareas computacionalmente intensivas (modelos ML, procesamiento de imagen), garantizando utilización eficiente de GPU/CPU y evitando bloqueos del event loop principal.

**Responsabilidades**:

**Gestión de colas por prioridad y tipo de recurso:**

- `queue:realtime` — liveness detection (latencia < 1s, alta prioridad).
- `queue:gpu` — face match (ArcFace), deepfake detection (requiere GPU).
- `queue:cpu` — OCR, document processing, ELA (CPU-bound, paralelizable).
- `queue:async` — auditoría, logging, purga de datos (baja prioridad, no bloquea la respuesta).

**Gestión del pool:**

- Workers CPU como procesos Python separados (multiprocessing) para tareas CPU-bound, evitando el GIL.
- Workers GPU gestionados con CUDA streams para inferencia ML paralela.
- Auto-scaling: escalar número de workers según la profundidad de las colas (integración con Kubernetes HPA o docker-compose scaling).
- Prevención de starvation: los workers de alta prioridad no pueden monopolizar todos los recursos.

**Optimización de la ejecución de modelos:**

- Los modelos ML se cargan una sola vez en memoria al arrancar el worker y se reutilizan para todas las tareas (no recargar en cada petición).
- Batching dinámico: agrupar múltiples peticiones de inferencia en un solo batch cuando hay carga suficiente, maximizando el throughput de GPU.
- Warm-up de modelos al arrancar para eliminar la latencia de primera inferencia.

**Resiliencia:**

- Retry automático de tareas fallidas (hasta 3 intentos con backoff exponencial).
- Dead Letter Queue (DLQ) para tareas que fallan repetidamente, con alerta al `health_monitor_agent`.
- Timeout por tarea: si excede el tiempo máximo, se cancela y se registra.

**Entradas**: Tareas encoladas por el orquestador.

**Salidas**: Resultados de las tareas procesadas, devueltos al orquestador vía callback.

---

## 13. Agente Model Server (`model_server_agent`)

**Rol**: Servir los modelos de Machine Learning de forma optimizada, eficiente y escalable, desacoplando la lógica de inferencia del resto del backend.

**Responsabilidades**:

**Serving de modelos:**

- Exponer los modelos ML como microservicios con API gRPC (alto rendimiento) o REST interno.
- Gestionar múltiples modelos y versiones simultáneamente.
- Servir modelos en GPU con máxima utilización del hardware (CUDA, TensorRT).

**Optimización de inferencia:**

- Conversión de modelos a **ONNX** para portabilidad y compatibilidad entre frameworks.
- **TensorRT optimization**: compilar modelos para la GPU específica del servidor (hasta 3–5x de speedup sobre PyTorch nativo).
- **Quantización INT8/FP16**: reducir tamaño del modelo y aumentar velocidad de inferencia con mínima pérdida de precisión.
- **Batching dinámico**: agregar múltiples peticiones de inferencia en un mismo batch para maximizar el throughput de GPU.
- **Model caching en VRAM**: mantener los modelos activos en GPU para evitar tiempo de carga por petición.

**Gestión del ciclo de vida de modelos:**

- Carga y descarga de modelos en caliente sin downtime (hot-swap).
- A/B testing entre versiones de modelos: enrutar un % del tráfico a la nueva versión antes del rollout completo.
- Rollback inmediato si la nueva versión degrada métricas de precisión o rendimiento.
- Versionado de modelos: cada modelo se identifica por nombre + versión semántica.

**Monitorización de modelos:**

- Latencia de inferencia por modelo (p50, p95, p99).
- Throughput (inferences/second) por modelo y por GPU.
- Detección de model drift: alertar si la distribución de scores cambia significativamente respecto a la línea base (indica degradación del modelo o cambio en los datos de entrada).

**Entradas**: Peticiones de inferencia (imágenes, frames) desde el `worker_pool_agent`.

**Salidas**: Resultados de inferencia (scores, embeddings, detecciones).

**Tecnología recomendada**: **NVIDIA Triton Inference Server** (self-hosted, production-grade, soporta TensorRT + ONNX + PyTorch + TensorFlow); **TorchServe** como alternativa si no hay GPU NVIDIA.

---

## 14. Agente Health Monitor (`health_monitor_agent`)

**Rol**: Vigilar continuamente la salud de todos los componentes del sistema, detectar fallos proactivamente y coordinar la recuperación automática.

**Responsabilidades**:

**Health checks activos:**

- Liveness probes: verificar que cada servicio responde (HTTP `/health`) cada N segundos.
- Readiness probes: verificar que cada servicio está listo para recibir tráfico (no solo que está vivo).
- Deep health checks: verificar que los modelos ML están cargados y responden correctamente con un input sintético de prueba.
- Connectivity checks: verificar conectividad a PostgreSQL, Redis, MinIO.

**Circuit Breaker:**

- Estado por dependencia: `CLOSED` (normal), `OPEN` (dependencia fallando), `HALF_OPEN` (probando recuperación).
- Transiciones automáticas basadas en tasa de error y tiempo transcurrido.
- Notificar al `api_gateway_agent` cuando un circuito se abre para aplicar graceful degradation.

**Alertas y notificaciones:**

- Alertas en tiempo real cuando un servicio cae o supera umbrales de latencia.
- Canales configurables: Slack, PagerDuty, email, webhook.
- Agrupación de alertas para evitar alert storm cuando múltiples servicios fallan en cascada.
- Alertas de capacidad: cuando la cola de workers supera una profundidad crítica, o la GPU supera X% de utilización.

**Auto-healing:**

- Reiniciar automáticamente contenedores/pods que fallen sus liveness probes.
- Escalar automáticamente workers cuando la cola supera un umbral.
- Rebalancear carga entre instancias sanas cuando alguna cae.

**Modos de degradación:**

- Definir y ejecutar modos de fallback: si el model server GPU no está disponible, degradar a inferencia CPU (más lento, pero funcional).
- Modo de emergencia: solo checks mínimos para casos de alta certeza, bypasando módulos que no responden.

**Entradas**: Métricas y señales de todos los agentes y servicios.

**Salidas**: Estado de salud del sistema, alertas, comandos de auto-healing, cambios de estado de circuit breakers.

---

## 15. Agente de Seguridad (`security_agent`)

**Rol**: Garantizar la seguridad integral del sistema: cifrado, gestión de secretos, detección de intrusiones y cumplimiento normativo.

**Responsabilidades**:

**Gestión de secretos:**

- Centralizar todos los secretos (API keys, contraseñas de BBDD, claves de cifrado) en un gestor de secretos (HashiCorp Vault).
- Rotación automática de secretos con zero-downtime.
- Ningún secreto en variables de entorno en texto plano ni en el repositorio de código.
- Auditoría de todos los accesos a secretos.

**Cifrado de datos en reposo:**

- Imágenes almacenadas temporalmente en MinIO cifradas con AES-256.
- Datos de sesión sensibles en Redis cifrados campo a campo si contienen PII.
- Columnas sensibles en PostgreSQL cifradas con pgcrypto.
- Gestión del ciclo de vida de claves (key rotation) sin pérdida de datos.

**Cifrado en tránsito:**

- TLS 1.3 en todas las comunicaciones externas.
- mTLS (mutual TLS) en todas las comunicaciones internas entre microservicios (via service mesh: Istio o Linkerd).
- Gestión automatizada de certificados (cert-manager + Let's Encrypt o CA interna).

**Detección de intrusiones:**

- Analizar patrones de peticiones para detectar enumeración, fuerza bruta y exploración de la API.
- Detectar payloads maliciosos (archivos malformados intencionadamente, inyecciones).
- Integración con `api_gateway_agent` para bloqueo dinámico de IPs atacantes.

**Control de acceso interno:**

- RBAC para los propios microservicios del sistema.
- Service accounts con permisos mínimos por servicio (principio de mínimo privilegio).
- Audit trail de todas las acciones administrativas.

**Cumplimiento GDPR:**

- Implementar y verificar políticas de retención de datos.
- Gestionar el proceso de "derecho al olvido": borrado completo de datos de un usuario a petición.
- Generar informes de cumplimiento para auditorías externas.

**Entradas**: Peticiones de secretos, eventos de seguridad, peticiones de cifrado/descifrado.

**Salidas**: Secretos inyectados de forma segura, eventos registrados, alertas de intrusión, informes de cumplimiento.

---

## 16. Agente de Base de Datos (`database_agent`)

**Rol**: Gestionar todas las operaciones de persistencia de forma eficiente, resiliente y consistente.

**Responsabilidades**:

**Connection pooling:**

- Pool de conexiones a PostgreSQL via PgBouncer (modo transaction pooling) para evitar el coste de abrir conexión en cada operación.
- Pool sizing adaptado a la carga: mínimo, máximo y overflow configurables.
- Health check y timeout del pool.

**Alta disponibilidad:**

- Configuración Primary/Replica con replicación streaming de PostgreSQL.
- Read/write splitting: lecturas a réplicas, escrituras al primary.
- Failover automático si el primary cae (Patroni o repmgr).
- Backups automáticos: full backup diario + WAL archiving continuo para Point-in-Time Recovery (PITR).

**Migraciones:**

- Alembic para migraciones versionadas y reversibles.
- Aplicación automatizada en el CI/CD pipeline antes del despliegue.
- Validación de compatibilidad entre versión de esquema y versión de código.

**Optimización de queries:**

- Índices correctamente diseñados para los patrones de acceso (session_id, doc_number, timestamp).
- Queries lentas detectadas via `pg_stat_statements` y alertadas al `observability_agent`.
- Vacuuming y analyze gestionados para mantener el rendimiento del query planner.

**Gestión de datos temporales:**

- Particionado de tablas por fecha para sesiones y logs (mejora rendimiento y facilita la purga).
- Jobs de purga automática de sesiones expiradas y datos biométricos.

**Entradas**: Operaciones CRUD desde todos los agentes.

**Salidas**: Datos persistidos o recuperados; estado de salud del cluster de BBDD.

---

## 17. Agente de Observabilidad (`observability_agent`)

**Rol**: Proporcionar visibilidad completa del sistema en tiempo real (métricas, trazas distribuidas, logs centralizados) para detectar problemas de rendimiento y depurar incidencias.

**Responsabilidades**:

**Métricas (Prometheus + Grafana):**

- Recolectar métricas de todos los agentes: latencia, throughput, tasa de error, CPU/GPU/memoria.
- Métricas de negocio KYC: tasa de verificación exitosa, distribución de scores, tiempo medio por fase.
- Dashboards en Grafana por capa: infraestructura, pipeline KYC, modelos ML, seguridad.
- Alerting rules en Grafana Alertmanager.

**Trazabilidad distribuida (Jaeger o Grafana Tempo):**

- Propagar `trace_id` y `span_id` a través de todos los agentes.
- Registrar el tiempo de cada span (inicio y fin de cada agente) dentro de una sesión.
- Visualizar el flame graph completo de una sesión para identificar cuellos de botella.
- Sampling configurable: 100% en desarrollo, configurable en producción.

**Logs centralizados (Grafana Loki o ELK Stack):**

- Agregar logs de todos los servicios con indexación y búsqueda.
- Correlacionar logs por `session_id` y `trace_id`.
- Retención configurable por nivel (DEBUG vs. ERROR).
- Alertas sobre patrones de error (>N errores de un tipo en X minutos).

**SLO / SLA Tracking:**

- Definir y monitorizar los Service Level Objectives: tiempo de respuesta < 8s en p95, disponibilidad > 99.9%.
- Error budgets: cuánto margen queda para el SLO del mes en curso.
- Informes automáticos de cumplimiento de SLA.

**Entradas**: Métricas, spans y logs emitidos por todos los agentes y servicios.

**Salidas**: Dashboards en tiempo real, alertas, trazas para diagnóstico, informes de SLA.

---

## Matriz Completa de Interacciones entre Agentes

### Flujo KYC

| Agente Origen              | Agente Destino             | Dato Transmitido               |
| -------------------------- | -------------------------- | ------------------------------ |
| `capture_agent`            | `liveness_agent`           | Secuencia de frames validados  |
| `capture_agent`            | `document_processor_agent` | Imagen del documento en bruto  |
| `liveness_agent`           | `face_match_agent`         | Frame de selfie validado       |
| `document_processor_agent` | `ocr_agent`                | Imagen del documento procesada |
| `document_processor_agent` | `face_match_agent`         | Imagen del rostro del titular  |
| `ocr_agent`                | `antifraud_agent`          | Datos extraídos del documento  |
| `face_match_agent`         | `antifraud_agent`          | Score de similitud facial      |
| `document_processor_agent` | `antifraud_agent`          | Score de falsificación         |
| `liveness_agent`           | `antifraud_agent`          | Score de liveness              |
| `antifraud_agent`          | `decision_agent`           | Flags y score de fraude        |
| `decision_agent`           | `orchestrator_agent`       | Decisión final                 |
| `*`                        | `audit_agent`              | Todos los eventos del pipeline |

### Flujo de infraestructura

| Agente Origen          | Agente Destino        | Función                                                     |
| ---------------------- | --------------------- | ----------------------------------------------------------- |
| `api_gateway_agent`    | `orchestrator_agent`  | Forwarding de peticiones autenticadas y validadas           |
| `orchestrator_agent`   | `worker_pool_agent`   | Encolar tareas computacionalmente intensivas                |
| `worker_pool_agent`    | `model_server_agent`  | Peticiones de inferencia ML                                 |
| `cache_agent`          | Todos los agentes     | Datos cacheados (sesión, listas negras, config, embeddings) |
| `database_agent`       | Todos los agentes     | Persistencia y recuperación de datos                        |
| `security_agent`       | Todos los agentes     | Secretos, cifrado, validación de accesos                    |
| `health_monitor_agent` | `api_gateway_agent`   | Cambios en circuit breakers, servicios caídos               |
| `health_monitor_agent` | `worker_pool_agent`   | Comandos de escalado y recuperación                         |
| `*`                    | `observability_agent` | Emisión continua de métricas, spans y logs                  |
