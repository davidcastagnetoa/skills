---
name: rabbitmq_broker
description: Alternativa a Redis como broker con mejor routing y dead-letter queues
type: Framework
priority: Recomendada
mode: Self-hosted
---

# rabbitmq_broker

RabbitMQ es un message broker AMQP con soporte nativo de prioridades, dead-letter queues y routing avanzado. Alternativa a Redis broker cuando se necesitan garantías de entrega más estrictas.

## When to use

Usar como alternativa al Redis broker en el `worker_pool_agent` si se necesitan prioridades nativas de mensaje, dead-letter queues o routing basado en topic exchange.

## Instructions

1. Desplegar: `docker run -d rabbitmq:3-management`.
2. Configurar en Celery: `broker_url = 'amqp://user:pass@rabbitmq:5672//'`.
3. Configurar exchanges y queues con prioridad:
   ```python
   task_queues = [
       Queue('realtime', Exchange('realtime'), routing_key='realtime', queue_arguments={'x-max-priority': 10}),
   ]
   ```
4. Configurar DLQ: `queue_arguments={'x-dead-letter-exchange': 'dlx'}`.
5. Habilitar management plugin para dashboard en puerto 15672.
6. Configurar HA policy: `rabbitmqctl set_policy ha-all "" '{"ha-mode":"all"}'`.
7. Monitorizar con Prometheus plugin: `rabbitmq-plugins enable rabbitmq_prometheus`.

## Notes

- RabbitMQ consume más recursos que Redis broker (~200MB RAM base).
- Las prioridades nativas de RabbitMQ son superiores a múltiples colas de Redis.
- Usar Redis broker para V1 por simplicidad; migrar a RabbitMQ si se necesitan DLQ avanzadas.