---
name: opencv_capture
description: Procesamiento de imagen con OpenCV para validación de calidad y detección de bordes
---

# opencv_capture

OpenCV es la librería principal de visión computacional. En el capture_agent se usa para validación de calidad y detección de bordes del documento.

## When to use

Usar en todos los módulos de procesamiento de imagen del backend.

## Instructions

1. `pip install opencv-python-headless` (sin GUI, para servidor)
2. Cargar desde bytes: `nparr = np.frombuffer(image_bytes, np.uint8); img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)`
3. Redimensionar: `cv2.resize(img, (width, height), interpolation=cv2.INTER_LANCZOS4)`
4. Normalizar orientación usando EXIF antes de procesar.
5. Convertir a RGB: `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)`
6. Exponer funciones en `backend/utils/image_utils.py`.

## Notes

- Usar `opencv-python-headless` en servidores; `opencv-python` solo con display.
- NumPy es dependencia implícita.