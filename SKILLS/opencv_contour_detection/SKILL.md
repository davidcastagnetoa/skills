---
name: opencv_contour_detection
description: Detectar bordes y contornos del documento para segmentación y corrección de perspectiva
---

# opencv_contour_detection

La detección de contornos con OpenCV localiza el perímetro del documento en la imagen para extraerlo y procesarlo de forma aislada del fondo.

## When to use

Usar como primer paso en el `document_processor_agent` antes de cualquier otro procesamiento.

## Instructions

1. Convertir a escala de grises y ecualizar histograma: `gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)`.
2. Aplicar blur adaptativo: `blur = cv2.bilateralFilter(gray, 11, 17, 17)`.
3. Detectar bordes con Canny adaptativo (calcular thresholds automáticamente por percentiles).
4. Dilatar bordes para cerrar gaps: `kernel = np.ones((3,3), np.uint8); dilated = cv2.dilate(edges, kernel)`.
5. Encontrar contornos y filtrar por área mínima (el documento ocupa >20% de la imagen).
6. Seleccionar contorno cuadrilátero de mayor área.
7. Si YOLOv8 está disponible, usar su bounding box como región de interés antes de aplicar contornos.

## Notes

- Iluminación uniforme mejora significativamente la detección. Proporcionar feedback al usuario.
- Si la detección falla, solicitar nueva captura con instrucciones específicas.