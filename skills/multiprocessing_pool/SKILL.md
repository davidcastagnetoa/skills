---
name: multiprocessing_pool
description: Pool de procesos Python para tareas CPU-bound evitando el GIL
---

# multiprocessing_pool

`multiprocessing.Pool` crea procesos Python separados que evitan el GIL, permitiendo paralelismo real para tareas CPU-bound como procesamiento de imagen, OCR y análisis de textura.

## When to use

Usar en el `worker_pool_agent` para tareas CPU-bound que no requieren GPU: procesamiento de documentos, ELA, análisis de textura, normalización OCR. Los workers GPU usan CUDA streams en su lugar.

## Instructions

1. Configurar Celery con prefork pool (por defecto):
   ```python
   app.conf.worker_pool = 'prefork'
   app.conf.worker_concurrency = os.cpu_count()
   ```
2. Para tareas fuera de Celery:
   ```python
   from multiprocessing import Pool
   with Pool(processes=4) as pool:
       results = pool.map(process_document, images)
   ```
3. Configurar `maxtasksperchild=100` para evitar memory leaks.
4. Usar `concurrent.futures.ProcessPoolExecutor` como alternativa moderna.
5. No compartir modelos ML entre procesos; cada proceso carga su propia copia.
6. Configurar `worker_max_memory_per_child = 200000` (KB) para auto-restart.

## Notes

- El prefork pool de Celery ya usa multiprocessing internamente; no crear pools adicionales dentro de tasks.
- Para I/O-bound tasks, usar gevent o eventlet pool en lugar de prefork.
- El número de workers CPU debe ser <= número de cores disponibles.