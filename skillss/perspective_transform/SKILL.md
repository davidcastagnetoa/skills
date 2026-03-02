---
name: perspective_transform
description: Corrección de perspectiva del documento fotografiado en ángulo mediante transformación homográfica
---

# perspective_transform

La transformación de perspectiva (homografía) rectifica la imagen del documento para que aparezca como si hubiera sido fotografiado perfectamente de frente, mejorando la calidad del OCR y face match.

## When to use

Usar inmediatamente después de detectar los 4 vértices del documento con `opencv_contour_detection`.

## Instructions

1. Ordenar los 4 puntos esquina: top-left, top-right, bottom-right, bottom-left.
2. Calcular dimensiones del documento rectificado: `maxWidth = max(distance(br, bl), distance(tr, tl))`.
3. Definir puntos destino: `dst = np.array([[0,0],[maxWidth,0],[maxWidth,maxHeight],[0,maxHeight]])`.
4. Calcular matriz de transformación: `M = cv2.getPerspectiveTransform(src_pts, dst_pts)`.
5. Aplicar transformación: `warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))`.
6. Verificar que el resultado tiene las proporciones esperadas del tipo de documento (DNI: 85.6mm × 54mm = ratio 1.585).

## Notes

- Proporciones de referencia: DNI español (ID-1): 85.6 × 54mm; Pasaporte: 125 × 88mm.
- Un ratio muy diferente al esperado puede indicar documento falso o imagen incorrecta.