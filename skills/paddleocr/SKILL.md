---
name: paddleocr
description: OCR multiidioma de alta precisión completamente self-hosted para extracción de texto de documentos
type: ML Model
priority: Esencial
mode: Self-hosted
---

# paddleocr

PaddleOCR es el motor OCR principal del sistema. Ofrece alta precisión en múltiples idiomas e incluye detección de texto, reconocimiento y clasificación de orientación.

## When to use

Usar para extraer todos los campos de texto del documento: nombre, apellidos, fecha de nacimiento, número de documento, fecha de expiración, nacionalidad.

## Instructions

1. Instalar: `pip install paddlepaddle paddleocr`.
2. Inicializar con modelos en español/inglés: `ocr = PaddleOCR(use_angle_cls=True, lang='es', use_gpu=True)`.
3. Procesar imagen: `result = ocr.ocr(img_path, cls=True)`.
4. El resultado es una lista de `[[bounding_box], [text, confidence]]` para cada región de texto.
5. Filtrar por confianza mínima: `confidence > 0.8`.
6. Aplicar post-procesamiento: limpiar caracteres extraños, normalizar espacios.
7. Combinar con las regiones detectadas por YOLOv8 para extracción de campos específicos.
8. Para el MRZ, aplicar el parser ICAO separadamente sobre la región MRZ recortada.

## Notes

- Repositorio oficial: https://github.com/PaddlePaddle/PaddleOCR
- EasyOCR es la alternativa: `pip install easyocr` — misma interfaz, diferente precisión por idioma.
- Configurar `use_gpu=False` si no hay GPU disponible (mayor latencia esperada).