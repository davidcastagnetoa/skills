---
name: tesseract_ocr
description: Motor OCR open-source clásico como alternativa de fallback
type: ML Model
priority: Opcional
mode: Self-hosted
---

# tesseract_ocr

Tesseract OCR es el motor OCR open-source más maduro, mantenido por Google. Aunque menos preciso que PaddleOCR/EasyOCR en documentos complejos, es extremadamente rápido y ligero como tercer nivel de fallback.

## When to use

Usar en el `ocr_agent` como tercer motor de fallback cuando PaddleOCR y EasyOCR fallan o no están disponibles. Útil en modo de degradación cuando los recursos GPU son limitados.

## Instructions

1. Instalar: `apt install tesseract-ocr tesseract-ocr-spa` y `pip install pytesseract`.
2. Configurar: `pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'`.
3. Ejecutar OCR: `text = pytesseract.image_to_string(image, lang='spa+eng')`.
4. Para bounding boxes: `data = pytesseract.image_to_data(image, output_type=Output.DICT)`.
5. Pre-procesar imagen: binarizar con Otsu, aplicar deskew antes del OCR.
6. Usar PSM 6 para bloques de texto uniforme: `--psm 6`.
7. Filtrar resultados con confianza del campo `conf` > 60.

## Notes

- Tesseract requiere imágenes bien preprocesadas; sin CLAHE/sharpening los resultados son pobres.
- Instalar datos de idioma adicionales: `tesseract-ocr-fra`, `tesseract-ocr-deu`, etc.
- No usar para MRZ; es menos preciso que PaddleOCR en fuentes monoespaciadas.