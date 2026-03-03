---
name: onnx_runtime
description: Runtime de inferencia ONNX optimizado para modelos faciales y de documento con aceleración CPU/GPU
type: Library
priority: Esencial
mode: Self-hosted
---

# onnx_runtime

Configura ONNX Runtime como motor de inferencia optimizado para ejecutar modelos de reconocimiento facial (ArcFace), detección de vida (MiniFASNet) y procesamiento de documentos en formato ONNX. Proporciona aceleración transparente en CPU y GPU mediante Execution Providers, reduciendo la latencia de inferencia en el pipeline KYC.

## When to use

Usa esta skill cuando necesites configurar el runtime de inferencia ONNX dentro del **model_server_agent**. Aplica cuando los modelos ya estén exportados a formato ONNX y se requiera ejecutarlos con máxima eficiencia, seleccionando el Execution Provider adecuado (CPU, CUDA, TensorRT). Esta skill es independiente de la optimización TensorRT-ONNX y se centra en la configuración del runtime de inferencia.

## Instructions

1. Instalar ONNX Runtime con soporte GPU:
   ```bash
   pip install onnxruntime-gpu  # Para GPU con CUDA
   # o
   pip install onnxruntime      # Solo CPU
   ```

2. Crear una sesión de inferencia con el Execution Provider apropiado:
   ```python
   import onnxruntime as ort

   providers = [
       ('CUDAExecutionProvider', {
           'device_id': 0,
           'arena_extend_strategy': 'kNextPowerOfTwo',
           'gpu_mem_limit': 2 * 1024 * 1024 * 1024,  # 2GB
       }),
       'CPUExecutionProvider'
   ]
   session = ort.InferenceSession("models/arcface.onnx", providers=providers)
   ```

3. Configurar las opciones de sesión para optimizar el rendimiento:
   ```python
   sess_options = ort.SessionOptions()
   sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
   sess_options.intra_op_num_threads = 4
   sess_options.inter_op_num_threads = 2
   sess_options.enable_mem_pattern = True
   sess_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
   ```

4. Implementar el wrapper de inferencia para cada modelo del pipeline KYC:
   ```python
   class ONNXModelRunner:
       def __init__(self, model_path: str, providers: list):
           self.session = ort.InferenceSession(model_path, sess_options, providers=providers)
           self.input_name = self.session.get_inputs()[0].name

       def predict(self, input_tensor: np.ndarray) -> np.ndarray:
           return self.session.run(None, {self.input_name: input_tensor})[0]
   ```

5. Validar la correcta carga de modelos verificando los inputs/outputs esperados:
   ```python
   for inp in session.get_inputs():
       print(f"Input: {inp.name}, Shape: {inp.shape}, Type: {inp.type}")
   for out in session.get_outputs():
       print(f"Output: {out.name}, Shape: {out.shape}, Type: {out.type}")
   ```

6. Implementar un pool de sesiones para manejar concurrencia en las verificaciones simultáneas, evitando cuellos de botella en la inferencia.

7. Configurar logging de métricas de inferencia (latencia p50/p95/p99, throughput) para cada modelo servido por el runtime.

## Notes

- ONNX Runtime selecciona automáticamente el mejor Execution Provider disponible del listado proporcionado; siempre incluir `CPUExecutionProvider` como fallback.
- La configuración de `gpu_mem_limit` es esencial cuando se comparte GPU entre múltiples modelos del pipeline (ArcFace, liveness, anti-spoofing) para evitar errores de memoria.
- Esta skill se enfoca en el runtime de ejecución; para la conversión de modelos a formato ONNX, usar la skill `onnx_model_export`.
