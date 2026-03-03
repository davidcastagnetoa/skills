# Fase 2: Core ML Pipeline

**Agentes involucrados**: `liveness-agent`, `face-match-agent`, `document-processor-agent`, `ocr-agent`, `model-server-agent`

**Objetivo**: Implementar los 4 modulos de procesamiento ML/CV que forman el nucleo del pipeline KYC. Cada modulo se desarrolla de forma independiente con su propia interfaz, tests y modelos.

**Prerequisitos**: Fase 1 completada (FastAPI, PostgreSQL, Redis, MinIO, Celery funcionando).

---

## 2.1 Descarga y Gestion de Modelos ML

**Agente**: `model-server-agent`
**Skills**: `onnx_model_export`, `onnx_runtime`, `model_versioning`

### Tareas

- [x] Crear `scripts/download-models.sh` que descargue todos los modelos necesarios:
  ```
  models/
  ├── face_detection/
  │   └── retinaface_r50.onnx          # Deteccion de rostros
  ├── face_recognition/
  │   └── arcface_r100.onnx            # Embeddings faciales (ArcFace)
  ├── face_alignment/
  │   └── 2d106det.onnx                # Landmarks para alineacion
  ├── anti_spoofing/
  │   ├── silent_face_2.7_80x80.onnx   # MiniFASNet anti-spoofing
  │   └── silent_face_4_0_128x128.onnx
  ├── depth_estimation/
  │   └── midas_v21_small.onnx         # Estimacion de profundidad
  ├── document_detection/
  │   └── yolov8n_documents.onnx       # Deteccion/clasificacion de docs
  ├── ocr/
  │   ├── paddleocr_det.onnx           # Deteccion de texto
  │   ├── paddleocr_rec.onnx           # Reconocimiento de texto
  │   └── paddleocr_cls.onnx           # Clasificacion de orientacion
  └── deepfake/
      └── xceptionnet_ff.onnx          # Detector de deepfakes
  ```

- [x] Crear `models/checksums.json` con SHA256 de cada modelo para verificar integridad.

- [x] Agregar `models/` al `.gitignore` (modelos se descargan, no se commitean).

- [x] Crear base class para model loading con warm-up:
  ```python
  class BaseMLModel:
      def __init__(self, model_path: str):
          self.session = ort.InferenceSession(model_path)
          self._warmup()

      def _warmup(self):
          """Run dummy inference to pre-allocate memory"""
          ...

      async def predict(self, input: np.ndarray) -> np.ndarray:
          ...
  ```

### Checkpoint 2.1
> Resultado esperado: `./scripts/download-models.sh` descarga todos los modelos. Checksums verificados. Cada modelo se carga y ejecuta una inferencia dummy sin errores.

---

## 2.2 Modulo de Procesamiento de Documento

**Agente**: `document-processor-agent`
**Skills**: `opencv_contour_detection`, `document_edge_detection`, `perspective_transform`, `clahe`, `nonlocal_means_denoising`, `unsharp_mask_sharpening`, `yolov8_documents`, `ela_analysis`, `copy_move_forgery_detection`, `exif_metadata_analyzer`, `font_consistency_analyzer`, `esrgan_super_resolution`

### Tareas

- [ ] Implementar `DocumentDetector` — deteccion del documento en la imagen:
  - Deteccion de bordes con OpenCV (Canny + contour detection).
  - Clasificacion con YOLOv8: tipo de documento (DNI, pasaporte, licencia) y pais.
  - Recorte del ROI del documento.

- [ ] Implementar `PerspectiveCorrector` — correccion de perspectiva:
  - Detectar 4 esquinas del documento.
  - Aplicar transformacion homografica.
  - Normalizar a tamano estandar por tipo de documento.

- [ ] Implementar `ImageEnhancer` — mejora de imagen:
  - Denoising con Non-Local Means.
  - Normalizacion adaptativa CLAHE.
  - Sharpening con Unsharp Mask.
  - Ajuste de brillo/contraste.

- [ ] Implementar `FaceRegionExtractor` — extraccion del rostro del titular:
  - Localizar la foto del titular en el documento.
  - Recortar y normalizar.
  - Aplicar super-resolucion (ESRGAN) si la calidad es baja.

- [ ] Implementar `ForgeryDetector` — deteccion de manipulacion:
  - Error Level Analysis (ELA) para detectar regiones editadas.
  - Copy-Move Forgery Detection para regiones clonadas.
  - Analisis EXIF para detectar software de edicion.
  - Analisis de consistencia tipografica (Font Consistency).
  - Analisis de artefactos de compresion.

- [ ] Crear `DocumentProcessorService` que orqueste todos los sub-componentes:
  ```python
  class DocumentProcessorService:
      async def process(self, image: bytes) -> DocumentProcessingResult:
          detected = await self.detector.detect(image)
          corrected = await self.corrector.correct(detected)
          enhanced = await self.enhancer.enhance(corrected)
          face_region = await self.face_extractor.extract(enhanced)
          forgery = await self.forgery_detector.analyze(image, enhanced)
          return DocumentProcessingResult(
              document_type=detected.doc_type,
              country=detected.country,
              processed_image=enhanced,
              face_region=face_region,
              forgery_score=forgery.score,
              detected_anomalies=forgery.anomalies,
          )
  ```

- [ ] Tests unitarios para cada sub-componente con imagenes de prueba.

### Checkpoint 2.2
> Resultado esperado: Dado una imagen de un DNI/pasaporte, el modulo detecta el documento, corrige perspectiva, mejora la imagen, extrae el rostro del titular y detecta manipulaciones. Score de forgery < 0.3 para documentos legítimos, > 0.7 para documentos manipulados (con imagenes de test).

---

## 2.3 Modulo OCR

**Agente**: `ocr-agent`
**Skills**: `paddleocr`, `easyocr`, `tesseract_ocr`, `mrz_parser`, `regex_data_normalizer`, `cross_field_consistency_checker`, `document_expiry_validator`

### Tareas

- [ ] Implementar `OCREngine` con PaddleOCR como motor principal:
  - Deteccion de regiones de texto.
  - Reconocimiento de caracteres.
  - Confidence score por campo.

- [ ] Implementar fallback chain: PaddleOCR → EasyOCR → Tesseract.

- [ ] Implementar `MRZParser` — parser de Machine Readable Zone:
  - Detectar la zona MRZ en la imagen (2 o 3 lineas de texto OCR-B).
  - Parsear campos segun ICAO 9303.
  - Validar checksums (check digits) del MRZ.
  - Extraer: nombre, nacionalidad, fecha nacimiento, sexo, fecha expiracion, numero documento.

- [ ] Implementar `DataNormalizer` — normalizacion de datos:
  - Fechas a formato ISO 8601.
  - Nombres: eliminar caracteres especiales, normalizar mayusculas.
  - Numeros de documento: eliminar espacios, guiones.

- [ ] Implementar `ConsistencyChecker`:
  - Cruzar datos MRZ con campos visuales (VIZ) del documento.
  - Detectar discrepancias nombre MRZ vs nombre impreso.
  - Verificar coherencia de fechas.
  - Score de consistencia 0-1.

- [ ] Implementar `ExpiryValidator`:
  - Verificar que el documento no esta caducado.
  - Flag de warning si caduca en < 30 dias.

- [ ] Crear `OCRService` que orqueste todo:
  ```python
  class OCRService:
      async def extract(self, image: bytes) -> OCRResult:
          raw_text = await self.engine.recognize(image)
          mrz = await self.mrz_parser.parse(image)
          normalized = self.normalizer.normalize(raw_text, mrz)
          consistency = self.consistency_checker.check(normalized, mrz)
          expiry = self.expiry_validator.validate(normalized.expiry_date)
          return OCRResult(
              fields=normalized,
              mrz_data=mrz,
              mrz_valid=mrz.is_valid,
              data_consistency_score=consistency.score,
              is_expired=expiry.is_expired,
          )
  ```

- [ ] Tests con imagenes de documentos reales (anonimizados) y sinteticos.

### Checkpoint 2.3
> Resultado esperado: Dado un documento procesado, el modulo extrae todos los campos, parsea MRZ con checksums validos, normaliza datos y detecta inconsistencias. Accuracy > 95% en campos de texto.

---

## 2.4 Modulo de Deteccion de Vida (Liveness)

**Agente**: `liveness-agent`
**Skills**: `silent_face_anti_spoofing`, `minifasnet`, `ear_blink_detection`, `head_pose_estimation`, `smile_expression_detector`, `optical_flow_farneback`, `midas_depth_estimation`, `lbp_fourier_texture`, `rppg_pulse_detection`, `xceptionnet_gan_detector`, `faceforensics_classifier`, `random_challenge_sequencer`, `temporal_compliance_validator`, `mediapipe_face_mesh`

### Tareas

#### 2.4.1 Liveness Pasivo
- [ ] Implementar `TextureAnalyzer` — analisis de micro-textura:
  - Local Binary Patterns (LBP) para detectar textura de papel/pantalla.
  - Analisis de frecuencias Fourier para patrones de moire.
  - Score de "realidad" de la textura de piel.

- [ ] Implementar `DepthEstimator` — estimacion de profundidad:
  - MiDaS v2.1 small para mapa de profundidad monocular.
  - Verificar que el rostro tiene profundidad 3D coherente (no plano como foto/pantalla).
  - Score de profundidad.

- [ ] Implementar `AntiSpoofingModel` — modelo de anti-spoofing:
  - Silent-Face-Anti-Spoofing (MiniFASNet) como modelo principal.
  - Clasificacion: real vs. spoof (foto, pantalla, mascara).
  - Score de liveness pasivo.

- [ ] Implementar `DeepfakeDetector` — deteccion de deepfakes:
  - XceptionNet entrenado en FaceForensics++.
  - Detectar artefactos GAN, face swap, face reenactment.
  - Score de autenticidad.

- [ ] Implementar `OpticalFlowAnalyzer` — analisis de movimiento:
  - Farneback optical flow entre frames consecutivos.
  - Detectar movimiento no natural (video en loop, imagen estatica).
  - Detectar movimiento uniforme (toda la imagen se mueve igual = pantalla).

#### 2.4.2 Liveness Activo (Challenge-Response)
- [ ] Implementar `ChallengeSequencer` — generador de desafios:
  - Pool de desafios: parpadeo, giro izquierda, giro derecha, sonrisa, subir cejas.
  - Secuencia aleatoria de 2-3 desafios por sesion.
  - Nunca repetir la misma secuencia consecutivamente.

- [ ] Implementar `BlinkDetector` — deteccion de parpadeo:
  - Eye Aspect Ratio (EAR) con MediaPipe Face Mesh landmarks.
  - Detectar parpadeo natural (duracion 100-400ms).
  - Rechazar parpadeos demasiado rapidos o lentos (mecanicos).

- [ ] Implementar `HeadPoseEstimator` — estimacion de orientacion:
  - Calcular yaw, pitch, roll con landmarks faciales.
  - Verificar que el usuario gira la cabeza en la direccion solicitada.
  - Umbral de angulo minimo para considerar el giro valido.

- [ ] Implementar `ExpressionDetector` — deteccion de expresiones:
  - Detectar sonrisa usando distancia entre landmarks de boca.
  - Detectar cejas levantadas.

- [ ] Implementar `TemporalValidator` — validacion temporal:
  - Verificar que los desafios se completan en orden.
  - Verificar que el tiempo de respuesta es humano (no demasiado rapido ni lento).
  - Verificar continuidad del rostro entre desafios (mismo rostro todo el tiempo).

#### 2.4.3 Integracion
- [ ] Crear `LivenessService` que combine pasivo + activo:
  ```python
  class LivenessService:
      async def analyze(self, frames: list[np.ndarray]) -> LivenessResult:
          # Pasivo (sobre todos los frames)
          texture = await self.texture_analyzer.analyze(frames)
          depth = await self.depth_estimator.estimate(frames[0])
          anti_spoof = await self.anti_spoofing.predict(frames)
          deepfake = await self.deepfake_detector.predict(frames)
          optical_flow = await self.optical_flow.analyze(frames)

          # Activo (sobre secuencia de challenge-response)
          challenges = self.challenge_sequencer.generate()
          challenge_results = await self.validate_challenges(frames, challenges)

          passive_score = weighted_average([texture, depth, anti_spoof, deepfake, optical_flow])
          active_score = challenge_results.score

          return LivenessResult(
              is_live=passive_score > 0.7 and active_score > 0.8,
              liveness_score=combined_score(passive_score, active_score),
              attack_type_detected=detect_attack_type(...)
              challenge_passed=challenge_results.all_passed,
          )
  ```

- [ ] Tests con datasets de spoofing (NUAA, CASIA-FASD si disponible) y videos reales.

### Checkpoint 2.4
> Resultado esperado: El modulo detecta correctamente fotos impresas, pantallas y videos reproducidos con > 99% de precision. Challenge-response funciona con parpadeo y giro de cabeza. Score de liveness < 0.3 para ataques, > 0.8 para personas reales.

---

## 2.5 Modulo de Comparacion Facial (Face Match)

**Agente**: `face-match-agent`
**Skills**: `insightface_arcface`, `facenet_backup`, `deepface_framework`, `mediapipe_face_alignment`, `mediapipe_face_mesh`, `cosine_similarity`, `esrgan_super_resolution`, `age_progression_compensation`

### Tareas

- [ ] Implementar `FaceDetector` — deteccion de rostros:
  - RetinaFace para deteccion precisa.
  - Verificar que hay exactamente 1 rostro.
  - Bounding box + 5 key landmarks.

- [ ] Implementar `FaceAligner` — alineacion facial:
  - Alineacion con 5 landmarks (ojos, nariz, comisuras).
  - Crop y resize a 112x112 (input de ArcFace).

- [ ] Implementar `EmbeddingGenerator` — generacion de embeddings:
  - ArcFace (InsightFace, modelo R100) como modelo principal.
  - FaceNet como backup/fallback.
  - Output: vector de 512 dimensiones.
  - Normalizar embeddings a norma unitaria.

- [ ] Implementar `FaceMatcher` — comparacion:
  - Similitud coseno entre embedding de selfie y embedding de documento.
  - Umbrales configurables:
    - > 0.85: MATCH
    - 0.70 - 0.85: REVIEW
    - < 0.70: NO_MATCH

- [ ] Implementar `QualityCompensator`:
  - Compensar diferencia de calidad entre foto de documento (baja res) y selfie (alta res).
  - Super-resolucion ESRGAN en foto de documento si es necesario.
  - Ajuste de embeddings por calidad.

- [ ] Crear `FaceMatchService`:
  ```python
  class FaceMatchService:
      async def compare(self, selfie: bytes, document_face: bytes) -> FaceMatchResult:
          selfie_face = await self.detector.detect(selfie)
          doc_face = await self.detector.detect(document_face)
          # Super-res si la calidad del documento es baja
          if doc_face.quality < 0.5:
              doc_face = await self.super_resolution.enhance(doc_face)
          selfie_aligned = await self.aligner.align(selfie_face)
          doc_aligned = await self.aligner.align(doc_face)
          selfie_emb = await self.embedding.generate(selfie_aligned)
          doc_emb = await self.embedding.generate(doc_aligned)
          similarity = cosine_similarity(selfie_emb, doc_emb)
          return FaceMatchResult(
              match=similarity > self.threshold,
              similarity_score=similarity,
              confidence=calculate_confidence(similarity),
          )
  ```

- [ ] Tests con pares de imagenes: misma persona (positivos), personas diferentes (negativos).

### Checkpoint 2.5
> Resultado esperado: FAR < 0.1%, FRR < 5% medido sobre un set de test de al menos 100 pares. Tiempo de inferencia < 500ms por par.

---

## 2.6 Integracion de Modulos como Celery Tasks

**Agente**: `worker-pool-agent`
**Skills**: `celery`, `celery_redis`, `celery_canvas`

### Tareas

- [ ] Registrar cada modulo como Celery task:
  ```python
  @celery_app.task(queue='cpu', bind=True, max_retries=2)
  def process_document(self, session_id: str, image_data: bytes):
      ...

  @celery_app.task(queue='gpu', bind=True, max_retries=2)
  def run_face_match(self, session_id: str, selfie: bytes, doc_face: bytes):
      ...

  @celery_app.task(queue='gpu', bind=True, max_retries=2)
  def run_liveness(self, session_id: str, frames: list[bytes]):
      ...

  @celery_app.task(queue='cpu', bind=True, max_retries=2)
  def run_ocr(self, session_id: str, doc_image: bytes):
      ...
  ```

- [ ] Configurar colas separadas: `realtime`, `gpu`, `cpu`, `async`.

- [ ] Configurar timeouts por tarea (liveness: 3s, face_match: 3s, ocr: 5s, doc_processing: 5s).

- [ ] Implementar retry con backoff exponencial para fallos transitorios.

- [ ] Test de integracion: enviar tarea, recibir resultado.

### Checkpoint 2.6
> Resultado esperado: Cada modulo se ejecuta como Celery task en su cola correspondiente. Timeouts y retries funcionan correctamente.

---

## Criterios de Completitud de Fase 2

- [ ] Los 4 modulos (doc_processing, OCR, liveness, face_match) funcionan de forma independiente
- [ ] Cada modulo tiene tests unitarios con cobertura > 80%
- [ ] Modelos ML se descargan, cargan y ejecutan correctamente
- [ ] Cada modulo esta registrado como Celery task
- [ ] Metricas de rendimiento medidas:
  - doc_processing < 2s
  - OCR < 2s
  - liveness < 2s
  - face_match < 500ms por par
- [ ] FAR < 0.1%, FRR < 5% en face match
- [ ] Tasa de deteccion de spoofing > 99% en liveness
