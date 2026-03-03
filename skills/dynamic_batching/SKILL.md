---
name: dynamic_batching
description: Agrupar peticiones de inferencia en batches cuando la cola supera un umbral
---

# dynamic_batching

Agrupamiento dinámico de múltiples peticiones de inferencia en un solo batch GPU para maximizar throughput. Cuando llegan varias peticiones simultáneamente, se procesan juntas en vez de una por una.

## When to use

Usar en el `worker_pool_agent` cuando hay carga sostenida (>10 peticiones/segundo). En baja carga, procesar individualmente para mínima latencia.

## Instructions

1. Implementar colector de batch con timeout:
   ```python
   batch = []
   while len(batch) < max_batch_size:
       try:
           item = await queue.get(timeout=max_wait_ms / 1000)
           batch.append(item)
       except asyncio.TimeoutError:
           break
   ```
2. Configurar `max_batch_size=8` y `max_wait_ms=50`.
3. Concatenar inputs: `batch_tensor = torch.stack([item.tensor for item in batch])`.
4. Ejecutar inferencia en batch: `results = model(batch_tensor)`.
5. Distribuir resultados: cada item recibe su resultado individual.
6. Monitorizar batch_size promedio: si siempre es 1, el batching no aporta valor.
7. Ajustar max_batch_size según VRAM disponible.

## Notes

- Triton Inference Server implementa dynamic batching automáticamente; preferir Triton si está disponible.
- El batch size máximo depende de la VRAM: ArcFace batch=8 consume ~2GB.
- El max_wait_ms añade latencia; balance entre throughput (batch grande) y latencia (batch pequeño).