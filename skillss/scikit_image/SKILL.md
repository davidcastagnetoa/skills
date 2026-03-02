---
name: scikit_image
description: Algoritmos avanzados de procesamiento de imagen para análisis de documentos
---

# scikit_image

scikit-image complementa a OpenCV con algoritmos de procesamiento de imagen de más alto nivel: análisis de estructuras locales, detección de patrones, métricas de calidad (SSIM) y análisis de frecuencia para detección de manipulaciones.

## When to use

Usar para algoritmos que no están en OpenCV o que tienen mejor implementación en scikit-image: SSIM para comparar imágenes, análisis LBP para textura, watershed para segmentación avanzada.

## Instructions

1. Instalar: `pip install scikit-image`
2. SSIM para detectar manipulación comparando documento contra plantilla:
   ```python
   from skimage.metrics import structural_similarity as ssim
   def compare_with_template(doc_img: np.ndarray, template: np.ndarray) -> float:
       # Redimensionar al mismo tamaño
       resized = cv2.resize(doc_img, (template.shape[1], template.shape[0]))
       score, _ = ssim(cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY),
                       cv2.cvtColor(template, cv2.COLOR_BGR2GRAY), full=True)
       return score  # 1.0 = idéntico, <0.7 = muy diferente
   ```
3. LBP para análisis de textura de seguridad (microimpresión, guilloche):
   ```python
   from skimage.feature import local_binary_pattern
   def analyze_security_texture(region: np.ndarray) -> np.ndarray:
       gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
       lbp = local_binary_pattern(gray, P=8, R=1, method="uniform")
       hist, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10), density=True)
       return hist  # histograma de patrones de textura
   ```
4. Análisis de frecuencia con FFT para detectar patrones de moiré (señal de pantalla):
   ```python
   from skimage.filters import gabor
   def detect_moire_pattern(img: np.ndarray) -> float:
       gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(float) / 255
       freal, _ = gabor(gray, frequency=0.3)
       return float(np.std(freal))  # alta varianza = posible moiré
   ```

## Notes

- scikit-image usa convenciones de array diferentes a OpenCV: float [0,1] vs uint8 [0,255] — convertir antes de mezclar.
- El análisis SSIM contra plantilla requiere tener plantillas para cada tipo de documento soportado — construir una librería de plantillas.
- gabor filter para detección de moiré es experimental — calibrar el threshold en un dataset real de ataques con pantalla.