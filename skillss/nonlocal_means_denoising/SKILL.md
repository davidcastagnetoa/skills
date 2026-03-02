---
name: nonlocal_means_denoising
description: Reducción de ruido preservando bordes y texto del documento para mejorar la calidad del OCR
---

# nonlocal_means_denoising

Non-Local Means (NLM) es el algoritmo de denoising más efectivo para documentos. A diferencia del blur gaussiano, preserva los bordes nítidos del texto mientras elimina el ruido granular.

## When to use

Aplicar después de CLAHE y antes de OCR, especialmente en documentos fotografiados con poca luz.

## Instructions

1. Usar OpenCV NLM (incluido en `opencv-python-headless`):
   ```python
   import cv2
   def denoise_document(img):
       # Para imagen en color
       return cv2.fastNlMeansDenoisingColored(img, None, h=10, hColor=10,
           templateWindowSize=7, searchWindowSize=21)
   def denoise_grayscale(gray):
       # Para escala de grises (más rápido, suficiente para OCR)
       return cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
   ```
2. Ajustar `h` según calidad: `h=5` para ruido leve, `h=15` para ruido severo.
3. Aplicar NLM DESPUÉS de perspectiva y ANTES de Unsharp Mask.
4. Para imágenes de alta resolución (>2MP), redimensionar primero.
5. Pipeline completo: `CLAHE → NLM Denoising → Unsharp Mask → [Otsu Binarization] → OCR`.

## Notes

- `fastNlMeansDenoisingColored` es ~5x más lento que la versión grayscale.
- Si la latencia es crítica, usar `cv2.bilateralFilter` como alternativa más rápida (menor calidad).