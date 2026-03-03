---
name: silent_face_anti_spoofing
description: Modelo de liveness pasivo NUAA para detectar ataques de impresión, pantalla y spoofing sin interacción del usuario
type: ML Model
priority: Esencial
mode: Self-hosted
---

# silent_face_anti_spoofing

Silent-Face-Anti-Spoofing (NUAA) es el modelo principal de liveness pasivo. Analiza un único frame para determinar si el rostro es real o un ataque (foto impresa, pantalla, máscara).

## When to use

Ejecutar sobre cada frame de selfie antes del challenge activo. Es la primera línea de defensa contra spoofing.

## Instructions

1. Clonar el repositorio: `git clone https://github.com/minivision-ai/Silent-Face-Anti-Spoofing.git`
2. Instalar dependencias: `pip install torch torchvision opencv-python`.
3. Descargar los pesos preentrenados del repositorio oficial (modelos 2.7_80x80 y 4_0_0_80x80).
4. Cargar ambos modelos en memoria al arrancar el worker (model warm-up).
5. Preprocesar el frame: recortar región facial, redimensionar a 80x80, normalizar.
6. Ejecutar inferencia en ambos modelos y promediar scores.
7. Umbral de liveness: `score > 0.6` = real; `score ≤ 0.6` = spoof.
8. Exportar a ONNX para despliegue en Triton: `torch.onnx.export(model, dummy_input, 'silent_fas.onnx')`.

## Notes

- Repositorio oficial: https://github.com/minivision-ai/Silent-Face-Anti-Spoofing
- Combinar con MiniFASNet para mayor robustez.
- Fine-tuning recomendado con datos propios del dominio para reducir FRR.