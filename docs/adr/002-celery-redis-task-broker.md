# ADR-002: Celery + Redis como broker de tareas

- **Estado**: accepted
- **Fecha**: 2026-03-03
- **Autores**: software-architecture-agent

## Contexto

El pipeline KYC ejecuta tareas computacionalmente intensivas (inferencia ML en GPU, procesamiento de imagen con OpenCV, OCR) que no deben bloquear el event loop del servidor web. Se necesita un sistema de colas que permita despachar estas tareas a workers especializados, con soporte para prioridades, reintentos y timeouts.

## Opciones Evaluadas

### Opcion A: Celery + Redis como broker
- Pros: maduro y battle-tested, soporte nativo para colas por prioridad, retry con backoff, dead letter queues, monitoring con Flower, gran comunidad Python, Redis ya se usa para cache.
- Contras: Redis como broker no garantiza durabilidad ante crash (puede perder mensajes en memoria), no soporta message acknowledgment tan robusto como RabbitMQ.

### Opcion B: Celery + RabbitMQ como broker
- Pros: garantias de entrega mas fuertes (AMQP), routing avanzado, mejor para mensajeria compleja.
- Contras: un servicio adicional de infraestructura que mantener, mas complejo de configurar, Redis ya es necesario para cache/rate-limiting (duplicaria infraestructura).

### Opcion C: Apache Kafka
- Pros: durabilidad extrema, replay de eventos, alto throughput.
- Contras: overkill para el volumen esperado, complejidad operativa alta, no es un task queue (es un log distribuido), latencia mayor para tareas individuales.

### Opcion D: asyncio puro (sin task queue)
- Pros: sin dependencia adicional, menor complejidad.
- Contras: no escala horizontalmente, no hay retry nativo, un crash pierde todas las tareas en vuelo, no hay visibilidad de colas.

## Decision

**Celery con Redis como broker.**

Redis ya forma parte del stack para cache y rate limiting, lo que evita introducir un servicio adicional. La perdida potencial de mensajes ante crash de Redis es aceptable porque cada sesion de verificacion es independiente y el usuario puede reintentar. Las tareas ML no son idempotentes en el sentido estricto, pero si son reinvocables sin efectos secundarios.

Se configuran 4 colas separadas por tipo de recurso:
- `realtime`: liveness detection (latencia < 1s).
- `gpu`: face match, deepfake detection.
- `cpu`: OCR, document processing, ELA.
- `async`: auditoria, logging, purga de datos.

## Consecuencias

- Redis debe configurarse con persistencia AOF para minimizar perdida de mensajes.
- Si el volumen crece y se requiere durabilidad estricta, se puede migrar a RabbitMQ como broker sin cambiar el codigo de las tasks (solo configuracion de Celery).
- Workers GPU y CPU se despliegan como procesos separados con diferentes concurrency settings.
- Celery Beat gestiona las tareas periodicas (purga de imagenes cada 5 min).
