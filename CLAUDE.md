# CLAUDE.md — Contexto del Proyecto: Sistema de Verificación de Identidad

## 1. Visión General

Este proyecto consiste en construir un **sistema de verificación de identidad (KYC — Know Your Customer)** que confirme que la persona que presenta un documento de identidad es realmente quien dice ser, comparando el documento con una selfie tomada en tiempo real.

El sistema debe ser **altamente resistente a fraudes**, **preciso** y lo más **independiente posible de servicios externos**, evitando dependencias monopolísticas.

---

## 2. Objetivo Principal

> Dado un documento de identidad (DNI, pasaporte, etc.) y una selfie en vivo capturada desde el dispositivo del usuario, determinar con alta fiabilidad si el rostro del documento pertenece a la misma persona que está frente a la cámara.

---

## 3. Flujo de Verificación (Pipeline)

```
[1. Captura de selfie en vivo]
        ↓
[2. Detección de vida (Liveness Detection)]
        ↓
[3. Captura / subida del documento de identidad]
        ↓
[4. Extracción y validación del documento]
        ↓
[5. Extracción del rostro del documento]
        ↓
[6. Comparación biométrica facial (selfie vs. documento)]
        ↓
[7. Análisis antifraude global]
        ↓
[8. Decisión final: VERIFICADO / RECHAZADO / REVISIÓN MANUAL]
```

---

## 4. Módulos del Sistema

### 4.1 Módulo de Captura de Selfie en Vivo

- La imagen debe ser tomada **en el momento**, no subida desde galería.
- Se debe bloquear el acceso a la galería de fotos del dispositivo para este paso.
- El sistema debe capturar una secuencia de frames, no solo una imagen estática.
- Tecnología: WebRTC (web), CameraX/AVFoundation (móvil nativo).

### 4.2 Módulo de Detección de Vida (Anti-Spoofing / Liveness Detection)

Este es uno de los módulos más críticos. Debe detectar y rechazar intentos de engaño como:

- **Foto impresa** puesta ante la cámara.
- **Pantalla con foto** (teléfono, tablet, monitor).
- **Máscara 3D** o molde facial.
- **Deepfake / video** reproducido ante la cámara.
- **Foto recortada** con ojos animados (ataques de replay).

Técnicas a implementar:

| Técnica                                  | Descripción                                                              |
| ---------------------------------------- | ------------------------------------------------------------------------ |
| **Passive Liveness**                     | Análisis de textura, reflejo, profundidad y artefactos en un único frame |
| **Active Liveness (Challenge-Response)** | Pedir al usuario que parpadee, gire la cabeza, sonría o siga un punto    |
| **3D Depth Estimation**                  | Estimación de profundidad facial con cámara monocular (MiDaS, etc.)      |
| **Blink Detection**                      | Detección de parpadeo natural usando landmarks faciales                  |
| **Optical Flow Analysis**                | Detectar movimiento no natural o inconsistencias de movimiento de video  |
| **Micro-texture Analysis**               | Detectar patrones de papel/pantalla en la piel (frecuencias de Fourier)  |

### 4.3 Módulo de Captura y Procesamiento del Documento

- Captura guiada con overlay para alinear el documento.
- Detección de bordes del documento (OpenCV, contour detection).
- Corrección de perspectiva (homografía).
- Mejora de imagen: denoising, contraste, sharpening.
- Detección de manipulaciones en el documento:
  - Detección de clonado/copia de regiones (Error Level Analysis — ELA).
  - Análisis de consistencia de fuentes y formatos.
  - Verificación de elementos de seguridad (holograma, watermark UV — si aplica).

### 4.4 Módulo de Extracción OCR del Documento

- Extracción de campos: nombre, apellidos, fecha de nacimiento, número de documento, fecha de expiración, nacionalidad.
- Lectura de la **Zona de Lectura Mecánica (MRZ)** en pasaportes y DNIs.
- Validación de checksums del MRZ (estándar ICAO 9303).
- Tecnologías: Tesseract OCR, EasyOCR, PaddleOCR (self-hosted), o modelos fine-tuned.

### 4.5 Módulo de Reconocimiento y Comparación Facial

- Extracción del rostro de la selfie y del documento.
- Generación de embeddings faciales.
- Cálculo de similitud coseno entre embeddings.
- Umbral de aceptación configurable (recomendado > 0.85 para alta seguridad).
- Modelos recomendados (self-hosted): **DeepFace**, **InsightFace (ArcFace)**, **FaceNet**, **dlib**.

### 4.6 Módulo Antifraude y Detección de Anomalías

Capas adicionales de verificación:

- **Consistencia foto-documento**: La foto del documento debe ser coherente con la edad indicada en el mismo.
- **Análisis de metadatos EXIF**: Si la imagen tiene metadatos, verificar que no indiquen edición.
- **Detección de GAN/Deepfake en selfie**: Usar clasificadores de imágenes sintéticas (e.g., modelos fine-tuned en FaceForensics++).
- **Geolocalización**: Verificar si la IP/geolocalización es coherente con la nacionalidad del documento (señal auxiliar, no bloqueante).
- **Rate limiting y detección de intentos múltiples**: Limitar reintentos por dispositivo/IP.
- **Análisis de iluminación**: Detectar iluminación artificial forzada que sugiera spoofing.

### 4.7 Motor de Decisión

- Score compuesto de todos los módulos (cada módulo emite una puntuación 0–1).
- Reglas configurables: umbrales de rechazo automático, aprobación automática, revisión manual.
- Logging completo para auditoría.
- Respuesta estructurada: `{ status, confidence_score, reasons[], timestamp, session_id }`.

---

## 5. Arquitectura Técnica

### 5.1 Stack Tecnológico Recomendado

| Capa                        | Tecnología                                                                |
| --------------------------- | ------------------------------------------------------------------------- |
| **Backend**                 | Python (FastAPI)                                                          |
| **Frontend/Móvil**          | React Native o Flutter (acceso nativo a cámara)                           |
| **Reconocimiento facial**   | InsightFace (ArcFace) — self-hosted                                       |
| **Liveness Detection**      | Silent-Face-Anti-Spoofing (NUAA) + Challenge-Response propio              |
| **OCR**                     | PaddleOCR o EasyOCR — self-hosted                                         |
| **Detección de documentos** | OpenCV + YOLOv8 fine-tuned para documentos                                |
| **Base de datos**           | PostgreSQL (datos de sesión), Redis (rate limiting)                       |
| **Almacenamiento temporal** | MinIO (S3-compatible, self-hosted) — imágenes se borran tras verificación |
| **Infraestructura**         | Docker + Kubernetes                                                       |

### 5.2 Servicios Externos Opcionales (con alternativas)

| Función          | Opción 1        | Opción 2       | Opción 3 |
| ---------------- | --------------- | -------------- | -------- |
| Liveness cloud   | AWS Rekognition | Azure Face API | Onfido   |
| OCR cloud        | Google Vision   | AWS Textract   | Mindee   |
| Face Match cloud | DeepAI          | BioID          | Kairos   |

> **Nota**: Se priorizan siempre las opciones self-hosted. Los servicios externos son fallback o para escalar.

---

## 6. Consideraciones de Seguridad y Privacidad

- Las imágenes **no deben almacenarse** más allá del tiempo necesario para la verificación (máximo 15 minutos).
- Todas las comunicaciones deben ir sobre **HTTPS/TLS 1.3**.
- Las imágenes deben transmitirse **cifradas**.
- Cumplimiento con **GDPR / LOPD** (para España/Europa).
- No se deben guardar embeddings biométricos sin consentimiento explícito.
- Los logs de auditoría deben ser anonimizados.

---

## 7. Criterios de Calidad y Rendimiento

| Métrica                           | Objetivo     |
| --------------------------------- | ------------ |
| **FAR (False Acceptance Rate)**   | < 0.1%       |
| **FRR (False Rejection Rate)**    | < 5%         |
| **Tiempo de respuesta total**     | < 8 segundos |
| **Tasa de detección de spoofing** | > 99%        |
| **Disponibilidad del servicio**   | > 99.9%      |

---

## 8. Casos de Uso de Fraude a Contemplar

1. Usuario presenta una foto impresa del DNI de otra persona.
2. Usuario muestra una pantalla con la selfie de otra persona.
3. Usuario usa una máscara o foto recortada.
4. Usuario usa un deepfake en tiempo real (filtros de cámara falsos).
5. Usuario intenta subir imágenes desde la galería en lugar de capturar en vivo.
6. Documento manipulado digitalmente (nombre o foto editados).
7. Documento caducado o de país no soportado.
8. Múltiples intentos con documentos distintos desde el mismo dispositivo.
9. Uso de VPN o proxies para enmascarar geolocalización.
10. Inyección de frames sintéticos en el flujo de video (bypass de cámara virtual).

---

## 9. Estructura del Repositorio

```
verifid/
├── backend/
│   ├── api/                  # Endpoints FastAPI
│   ├── modules/
│   │   ├── liveness/         # Detección de vida
│   │   ├── ocr/              # Extracción de texto del documento
│   │   ├── face_match/       # Comparación facial
│   │   ├── doc_processing/   # Procesamiento de imagen del documento
│   │   ├── antifraud/        # Análisis antifraude
│   │   └── decision/         # Motor de decisión
│   ├── models/               # Modelos ML (pesos, configs)
│   └── tests/
├── frontend/
│   ├── mobile/               # App React Native (Expo ~52)
│   │   ├── App.tsx           # Entry point
│   │   ├── app/
│   │   │   ├── types.ts      # Tipos compartidos
│   │   │   ├── navigation/AppNavigator.tsx
│   │   │   ├── screens/      # 7 pantallas (Welcome, SelfieCapture, ActiveChallenges, DocumentCapture, Processing, Result, Error)
│   │   │   ├── components/   # 6 componentes (FaceOval, FeedbackMessage, ChallengePrompt, DocumentGuide, ProgressIndicator, CameraOverlay)
│   │   │   ├── hooks/        # 4 hooks (useCamera, useFaceDetection, useVerification, useDeviceInfo)
│   │   │   ├── services/     # api.ts, deviceFingerprint.ts
│   │   │   └── utils/        # imageProcessing.ts, permissions.ts
│   │   ├── package.json
│   │   └── app.json
│   └── web/                  # App React (Vite + WebRTC)
│       ├── src/
│       │   ├── App.tsx       # Router con 6 rutas
│       │   ├── pages/        # 6 páginas (Welcome, SelfieCapture, Challenges, DocumentCapture, Processing, Result)
│       │   ├── hooks/        # useWebRTCCamera
│       │   ├── services/     # api.ts
│       │   └── types.ts
│       ├── index.html
│       └── package.json
├── infra/
│   ├── docker/
│   └── k8s/
├── docs/
│   └── plan/                 # Planes de implementación por fase (00-06)
├── CLAUDE.md
├── Agents.md
└── Skills.md
```

### 9.1 Estado de Implementación por Fase

| Fase | Nombre | Estado |
|------|--------|--------|
| 1 | Foundation | ✅ Completada |
| 2 | Core ML Pipeline | ✅ Completada |
| 3 | Pipeline Integration | ✅ Completada |
| 4 | Production Infra | ✅ Completada |
| 5 | Frontend (Mobile + Web) | ✅ Completada |
| 6 | Hardening | Pendiente |

---

## 10. Glosario

| Término                | Definición                                                             |
| ---------------------- | ---------------------------------------------------------------------- |
| **KYC**                | Know Your Customer — proceso de verificación de identidad              |
| **Liveness Detection** | Verificar que la persona es real y está presente en vivo               |
| **MRZ**                | Machine Readable Zone — zona legible de pasaportes/DNIs                |
| **FAR**                | False Acceptance Rate — tasa de impostores aceptados                   |
| **FRR**                | False Rejection Rate — tasa de usuarios legítimos rechazados           |
| **Embedding facial**   | Vector numérico que representa las características únicas de un rostro |
| **ELA**                | Error Level Analysis — técnica para detectar manipulación en imágenes  |
| **Spoofing**           | Intento de engañar al sistema con una imagen falsa                     |
| **ArcFace**            | Algoritmo de reconocimiento facial de estado del arte                  |
