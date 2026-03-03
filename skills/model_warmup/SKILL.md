---
name: model_warmup
description: Cargar modelos ML una sola vez al arrancar el worker
---

# model_warmup

Precarga de modelos ML en memoria al arrancar el worker para eliminar la latencia de primera inferencia. Los modelos se cargan una vez y se reutilizan para todas las tareas subsiguientes.

## When to use

Usar en el `worker_pool_agent` como signal handler de worker_init en Celery. Cada worker carga los modelos que necesita según su cola asignada al arrancar.

## Instructions

1. Implementar signal handler de Celery:
   ```python
   from celery.signals import worker_init

   models = {}

   @worker_init.connect
   def load_models(**kwargs):
       models['liveness'] = load_liveness_model()
       models['arcface'] = load_arcface_model()
       # Warm-up: una inferencia dummy para compilar JIT
       models['liveness'](torch.randn(1, 3, 80, 80).cuda())
   ```
2. Hacer inferencia dummy después de cargar para triggear compilación JIT/TensorRT.
3. Cargar solo los modelos de las colas asignadas al worker.
4. Configurar readiness probe que verifica que los modelos están cargados.
5. Log del tiempo de carga de cada modelo para monitorización.
6. Si un modelo falla al cargar, el worker no debe aceptar tareas de esa cola.

## Notes

- El warm-up dummy es crítico: la primera inferencia PyTorch puede ser 10x más lenta.
- En workers GPU, preasignar VRAM con `torch.cuda.empty_cache()` después del warm-up.
- El tiempo de carga típico es 5-30 segundos dependiendo del número de modelos.