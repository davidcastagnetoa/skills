revisa el contenido del proyecto actual, sobretodo el archivo CLAUDE.md, deseo desarrollar el proyecto, pero no dispongo de todas las skilles, solo algunas, en teoria el proyecto requiere 213 skilles (ver `231_list_skills.md`) pero solo dispongo de las listadas en la carpeta `list_skills`.

1. Verifica que las skiles disponibles sean suficientes.
2. Verifica que los agentes listados en `Agents.md` sean suficientes.
3. Si faltan skilles, crealas crealas en una carpeta llamada `pending_skills`.
4. Indicame como crear los agentes o hazlo tu mismo (tanto los agentes como las skilles son locales, es decir solo para el proyecto actual) NO GLOBALES.
5. Una vez disponga de las skilles y los agentes indicame como iniciar el desarrollo del proyecto.

NO respondas todas las peticiones a la vez, en cuanto acabes una pide confirmacion para la siguiente.
Aun no escribas codigo, primero quiero definidir el proceso que se llevara paso a paso (genera un plan de desarrollo detallado cuando ya se dispongan de todas las skiles y agentes necesarios).

---

Debido al limite diario, no has creado todas las skilles necesarias. Crea las skilles faltantes en la carpeta `pending_skills`. la skill `pending_skills/worker_pool_agent/celery_flower.md` quedo a medias, por favor revisa y completa la skill.

Las skills faltantes son:

- antifraud_agent (4)
  - blacklist_db
  - dex_mivolo_age_estimator
  - geoip2_maxmind
  - vpn_proxy_tor_detection

- api_gateway_agent (8)
  - api_key_management
  - graceful_degradation
  - gzip_brotli_compression
  - http2_support
  - request_timeout_management
  - retry_exponential_backoff
  - tls_1_3_termination
  - traefik

- architecture_agent (15)
  - archunit_import_linter
  - breaking_change_detector
  - chaos_toolkit
  - coupling_cohesion_metrics
  - datamodel_code_generator
  - dependabot_renovate
  - dependency_graph_analysis
  - drawio
  - json_schema_evolution
  - k6
  - plantuml_mermaid
  - pydantic_schema_registry
  - pytest_cov
  - technical_debt_backlog
  - technology_radar

- cache_agent (9)
  - cache_invalidation
  - cache_stampede_prevention
  - keyspace_notifications
  - lru_eviction_policy
  - redis_7
  - redis_cluster
  - redis_persistence
  - redis_py_async
  - ttl_management

- capture_agent (1)
  - camerax_avfoundation

- decision_agent (3)
  - decision_explainer
  - human_review_queue
  - weighted_score_aggregator

- document_processor_agent (1)
  - font_consistency_analyzer

- face_match_agent (2)
  - age_progression_compensation
  - deepface_framework

- liveness_agent (5)
  - compression_artifact_analysis
  - midas_depth_estimation
  - rppg_pulse_detection
  - smile_expression_detector
  - xceptionnet_gan_detector

- ocr_agent (5)
  - aws_textract
  - easyocr
  - google_vision_ocr
  - regex_data_normalizer
  - tesseract_ocr

- orchestrator_agent (1)
  - uuid_v4

- worker_pool_agent (8)
  - celery
  - celery_flower
  - cuda_streams
  - dynamic_batching
  - model_warmup
  - multiprocessing_pool
  - rabbitmq_broker
  - redis_broker
