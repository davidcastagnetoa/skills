revisa el contenido del proyecto actual, sobretodo el archivo CLAUDE.md, deseo desarrollar el proyecto, pero no dispongo de todas las skilles, solo algunas, en teoria el proyecto requiere 213 skilles (ver `231_list_skills.md`) pero solo dispongo de las listadas en la carpeta `list_skills`.

1. Verifica que las skiles disponibles sean suficientes.
2. Verifica que los agentes listados en `Agents.md` sean suficientes.
3. Si faltan skilles, crealas crealas en una carpeta llamada `pending_skills`.
4. Indicame como crear los agentes o hazlo tu mismo (tanto los agentes como las skilles son locales, es decir solo para el proyecto actual) NO GLOBALES.
5. Una vez disponga de las skilles y los agentes indicame como iniciar el desarrollo del proyecto.

NO respondas todas las peticiones a la vez, en cuanto acabes una pide confirmacion para la siguiente.
Aun no escribas codigo, primero quiero definidir el proceso que se llevara paso a paso (genera un plan de desarrollo detallado cuando ya se dispongan de todas las skiles y agentes necesarios).

---

Debido al limite diario, no has creado todas las skilles necesarias. Crea las skilles faltantes en la carpeta `pending_skills`. Cuando termines de crear las skilles faltantes. pasamos los siguientes pasos :

- 4. Indicarme como crear los agentes o hacerlo tu mismo (tanto los agentes como las skilles son locales, es decir solo para el proyecto actual) NO GLOBALES.
- 5. Una vez disponga de las skilles y los agentes indicame como iniciar el desarrollo del proyecto.

Recuerda: NO respondas todas las peticiones a la vez, en cuanto acabes una pide confirmacion para la siguiente.
Aun no escribas codigo, primero quiero definidir el proceso que se llevara paso a paso (genera un plan de desarrollo detallado cuando ya se dispongan de todas las skiles y agentes necesarios).

Las skills faltantes son:

- api_gateway_agent (4)
  - trace_id_propagation
  - prometheus_metrics_exporter
  - nginx_lua (separada de traefik)
  - traefik (separada de nginx)

- worker_pool_agent (6)
  - dead_letter_queue
  - prefetch_multiplier_tuning
  - celery (separada de celery_redis)
  - redis_broker (separada de celery_redis)
  - rabbitmq_broker (alternativa separada)
  - celery_flower (separada)

- model_server_agent (13)
  - torchserve
  - onnx_runtime
  - fp16_int8_quantization
  - onnx_model_export
  - grpc_server
  - model_versioning
  - ab_model_routing
  - model_drift_detection
  - gpu_utilization_monitoring
  - dynamic_batching_triton
  - triton_inference_server (separada)
  - tensorrt (separada de tensorrt_onnx)
  - onnx_runtime (separada de tensorrt_onnx)

- health_monitor_agent (9)
  - http_health_check_probes
  - deep_health_check
  - tenacity
  - kubernetes_liveness_readiness_probes
  - kubernetes_hpa
  - alertmanager
  - watchdog_supervisor
  - slo_error_budget_tracking
  - chaos_engineering (separada de chaos_toolkit)

- observability_agent (17)
  - prometheus_client
  - alertmanager (separada de prometheus)
  - node_exporter
  - dcgm_exporter
  - thanos
  - grafana_tempo
  - w3c_trace_context
  - trace_sampling
  - grafana_loki
  - promtail_vector
  - elk_stack
  - log_correlation
  - log_retention_policies
  - prometheus (separada de prometheus_grafana)
  - grafana (separada de prometheus_grafana)
  - opentelemetry_sdk (separada de opentelemetry_jaeger)
  - jaeger (separada de opentelemetry_jaeger)

- database_agent (14)
  - postgresql_16
  - asyncpg (separada de pgbouncer_asyncpg)
  - pgbouncer (separada de pgbouncer_asyncpg)
  - sqlalchemy_async (separada de postgresql_sqlalchemy_async)
  - postgresql (separada de postgresql_sqlalchemy_async)
  - alembic
  - patroni
  - pg_stat_statements
  - table_partitioning
  - connection_pool_sizing
  - pgbackrest
  - minio_server_side_encryption
  - minio_lifecycle_policies
  - minio_distributed_mode

- architecture_agent (3)
  - c4_model (separada de c4_model_structurizr)
  - structurizr_dsl (separada de c4_model_structurizr)
  - adr_tools (separada de adr_framework)
