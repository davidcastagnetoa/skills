---
name: pillow_pil
description: Librería base de procesamiento de imagen en Python — operaciones fundamentales de preprocesamiento de documentos
---

# pillow_pil

Pillow es la librería fundamental de procesamiento de imágenes en Python. Gestiona la carga, guardado, conversión de formato, redimensionado y manipulación básica de imágenes. Es una dependencia implícita de casi todos los otros componentes de procesamiento.

## When to use

Usar para todas las operaciones básicas de imagen antes de pasarlas a OpenCV o a los modelos ML: carga de archivos, conversión de formato, extracción de metadatos EXIF.

## Instructions

1. Instalar: `pip install Pillow`
2. Carga y validación básica:
   ```python
   from PIL import Image, ExifTags
   import io
   def load_and_validate(image_bytes: bytes) -> Image.Image:
       img = Image.open(io.BytesIO(image_bytes))
       img.verify()  # lanza excepción si el archivo está corrupto
       img = Image.open(io.BytesIO(image_bytes))  # reabrir tras verify()
       if img.mode != "RGB":
           img = img.convert("RGB")
       return img
   ```
3. Extraer metadatos EXIF para detectar edición:
   ```python
   def get_exif_data(img: Image.Image) -> dict:
       exif_data = img._getexif() or {}
       return {ExifTags.TAGS.get(k, k): v for k, v in exif_data.items()}
   ```
4. Conversión PIL ↔ NumPy/OpenCV: `np.array(pil_img)` y `Image.fromarray(cv2_img[:,:,::-1])`.
5. Verificar integridad del archivo: capturar `PIL.UnidentifiedImageError` para imágenes corruptas o no-imagen.
6. Redimensionar para normalizar antes del pipeline: `img.resize((width, height), Image.LANCZOS)`.

## Notes

- Siempre reabrir la imagen después de `img.verify()` — verify() consume el stream y deja la imagen en estado inconsistente.
- Pillow no preserva orientación EXIF al convertir — usar `ImageOps.exif_transpose(img)` para corregir rotación.
- Para imágenes muy grandes (>20MP), usar `img.thumbnail()` en lugar de `img.resize()` para respetar aspect ratio.