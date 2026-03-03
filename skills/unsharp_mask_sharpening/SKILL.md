---
name: unsharp_mask_sharpening
description: Aumentar nitidez del texto del documento con Unsharp Mask para maximizar la precisión del OCR
type: Algorithm
priority: Esencial
mode: Self-hosted
---

# unsharp_mask_sharpening

Unsharp Mask aumenta el contraste local en los bordes del texto, haciendo los caracteres más nítidos para el OCR. Es el estándar en pre-procesamiento de documentos.

## When to use

Aplicar como último paso de mejora de imagen, justo antes de pasar al `ocr_agent`.

## Instructions

1. Implementar con NumPy + OpenCV:
   ```python
   import cv2, numpy as np
   def unsharp_mask(img, sigma=1.0, strength=1.5):
       blurred = cv2.GaussianBlur(img, (0, 0), sigma)
       sharpened = cv2.addWeighted(img, 1.0 + strength, blurred, -strength, 0)
       return np.clip(sharpened, 0, 255).astype(np.uint8)
   ```
2. Parámetros recomendados para documentos: `sigma=1.0, strength=1.5`.
3. Aplicar sobre imagen en escala de grises para OCR:
   ```python
   gray = cv2.cvtColor(denoised_doc, cv2.COLOR_BGR2GRAY)
   sharpened = unsharp_mask(gray, sigma=1.0, strength=1.5)
   ```
4. Opcional: binarización Otsu después para texto puro blanco/negro:
   `_, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)`

## Notes

- Demasiado sharpening (`strength > 2.5`) introduce halos que empeoran el OCR.
- Para texto muy pequeño (campos MRZ), aumentar `strength=2.0`.