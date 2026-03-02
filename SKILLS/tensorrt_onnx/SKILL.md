---
name: tensorrt_onnx
description: Compilación y cuantización de modelos para GPU NVIDIA — hasta 5x speedup sobre PyTorch nativo
---

# tensorrt_onnx

TensorRT compila modelos ONNX para el hardware GPU específico del servidor, aplicando fusión de capas, cuantización FP16/INT8 y otras optimizaciones que reducen la latencia hasta 5x.

## When to use

Aplicar a todos los modelos ML antes del despliegue en producción en servidores con GPU NVIDIA.

## Instructions

1. Instalar: TensorRT viene incluido en el contenedor de Triton o instalar desde NVIDIA: `pip install tensorrt`.
2. Convertir ONNX a TensorRT engine:
   ```python
   import tensorrt as trt
   builder = trt.Builder(logger)
   config = builder.create_builder_config()
   config.set_flag(trt.BuilderFlag.FP16)  # Activar FP16
   network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
   parser = trt.OnnxParser(network, logger)
   parser.parse_from_file('model.onnx')
   engine = builder.build_serialized_network(network, config)
   with open('model.trt', 'wb') as f: f.write(engine)
   ```
3. Cargar engine en Triton con backend TensorRT.
4. Medir speedup: comparar latencia ONNX Runtime vs TensorRT con `perf_analyzer`.

## Notes

- El engine TensorRT es específico del GPU model; recompilar si cambia el hardware.
- INT8 requiere calibración con dataset representativo; FP16 es plug-and-play.
- `trtexec` — herramienta CLI de diagnóstico incluida en TensorRT.