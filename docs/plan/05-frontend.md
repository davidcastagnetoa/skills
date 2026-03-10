# Fase 5: Frontend

**Agentes involucrados**: `capture-agent` (parte frontend)

**Objetivo**: Desarrollar la aplicacion movil (React Native) y la version web que guian al usuario a traves del proceso de verificacion, capturan selfie en vivo y documento, y muestran resultados.

**Prerequisitos**: Fase 3 completada (pipeline backend funcional).

---

## 5.1 Arquitectura Frontend

### Stack

| Plataforma | Tecnologia |
|-----------|-----------|
| Movil (iOS + Android) | React Native con Expo |
| Web | React + WebRTC |
| Camara movil | CameraX (Android) / AVFoundation (iOS) via react-native-camera |
| Camara web | WebRTC navigator.mediaDevices |
| HTTP client | Axios / fetch |
| Estado | Zustand o React Context |
| UI Kit | React Native Paper o NativeBase |

### Estructura

```
frontend/
├── mobile/
│   ├── app/
│   │   ├── screens/
│   │   │   ├── WelcomeScreen.tsx
│   │   │   ├── SelfieCapture.tsx
│   │   │   ├── DocumentCapture.tsx
│   │   │   ├── ProcessingScreen.tsx
│   │   │   ├── ResultScreen.tsx
│   │   │   └── ErrorScreen.tsx
│   │   ├── components/
│   │   │   ├── CameraOverlay.tsx
│   │   │   ├── DocumentGuide.tsx
│   │   │   ├── FaceOval.tsx
│   │   │   ├── ChallengePrompt.tsx
│   │   │   ├── ProgressIndicator.tsx
│   │   │   └── FeedbackMessage.tsx
│   │   ├── hooks/
│   │   │   ├── useCamera.ts
│   │   │   ├── useFaceDetection.ts
│   │   │   ├── useVerification.ts
│   │   │   └── useDeviceInfo.ts
│   │   ├── services/
│   │   │   ├── api.ts
│   │   │   └── deviceFingerprint.ts
│   │   └── utils/
│   │       ├── imageProcessing.ts
│   │       └── permissions.ts
│   ├── package.json
│   └── app.json
└── web/
    ├── src/
    │   ├── pages/
    │   ├── components/
    │   ├── hooks/
    │   └── services/
    └── package.json
```

---

## 5.2 Flujo de UX

### Tareas

- [x] Disenar el flujo de pantallas:
  ```
  Welcome → Selfie Capture → Challenges → Document Capture → Processing → Result
  ```

- [x] Pantalla 1: **Welcome**
  - Explicar el proceso al usuario.
  - Solicitar permisos de camara.
  - Boton "Iniciar verificacion".

- [x] Pantalla 2: **Selfie Capture**
  - Ovalo facial en pantalla para guiar al usuario.
  - Feedback en tiempo real:
    - "Acerca tu rostro"
    - "Mejora la iluminacion"
    - "Mantente quieto"
  - Deteccion de rostro en tiempo real (on-device, MediaPipe).
  - Bloquear acceso a galeria — solo camara frontal en vivo.
  - Capturar secuencia de frames (3-5 segundos).

- [x] Pantalla 3: **Active Challenges**
  - Mostrar instrucciones de challenge: "Parpadea", "Gira la cabeza a la derecha".
  - Feedback visual de progreso.
  - Timeout si el usuario no responde en 10s.

- [x] Pantalla 4: **Document Capture**
  - Overlay con marco de documento (tamano DNI/pasaporte).
  - Guia visual para alinear el documento.
  - Deteccion automatica de bordes del documento.
  - Captura automatica cuando el documento esta bien alineado.
  - Feedback: "Acerca el documento", "Evita reflejos", "Mantente estable".
  - Solo camara trasera.

- [x] Pantalla 5: **Processing**
  - Indicador de progreso por fase del pipeline.
  - Animacion de "verificando...".
  - Polling o WebSocket para recibir resultado.

- [x] Pantalla 6: **Result**
  - VERIFIED: check verde, mensaje de exito.
  - REJECTED: X roja, motivo legible.
  - MANUAL_REVIEW: reloj, "Tu verificacion esta en revision".
  - Opcion de reintentar si fue rechazado por calidad de imagen.

### Checkpoint 5.2 ✅ COMPLETADO
> Resultado esperado: Flujo completo navegable con mockups/wireframes aprobados.
> Completado: 6 pantallas + ErrorScreen + AppNavigator + App.tsx entry point.

---

## 5.3 Captura de Selfie (Movil)

**Skills**: `camerax_avfoundation`, `webrtc_media_devices`, `mediapipe_face_detection`

### Tareas

- [x] Implementar acceso a camara frontal con react-native-camera o expo-camera:
  - Solo camara frontal, no galeria.
  - Configurar resolucion minima 640x480.
  - Deshabilitar flash.

- [x] Implementar deteccion de rostro on-device:
  - MediaPipe Face Detection via TFLite o react-native-mlkit.
  - Verificar que hay exactamente 1 rostro en el frame.
  - Verificar que el rostro esta dentro del ovalo guia.

- [x] Implementar captura de secuencia de frames:
  - Capturar 1 frame cada 200ms durante 3-5 segundos.
  - Almacenar frames en memoria (no en disco).
  - Enviar como array de base64 al backend.

- [x] Implementar device fingerprinting:
  - Recopilar: modelo de dispositivo, OS version, app version, screen size.
  - Hash SHA256 del fingerprint.

### Checkpoint 5.3 ✅ COMPLETADO
> Resultado esperado: La app captura selfie en vivo con deteccion de rostro en tiempo real. Solo se puede usar la camara, no la galeria.
> Completado: SelfieCapture.tsx + useCamera hook + useFaceDetection hook + FaceOval component + deviceFingerprint service.

---

## 5.4 Captura de Documento (Movil)

### Tareas

- [x] Implementar captura de documento con camara trasera:
  - Overlay con marco de tamano documento.
  - Auto-focus habilitado.
  - Flash opcional (LED del telefono).

- [x] Implementar deteccion de bordes del documento on-device:
  - OpenCV.js o libreria nativa para deteccion de contornos.
  - Captura automatica cuando los 4 bordes son detectados.
  - Feedback visual en tiempo real.

- [x] Implementar validacion basica de calidad on-device:
  - Blur detection.
  - Brillo minimo/maximo.
  - Resolucion minima.

### Checkpoint 5.4 ✅ COMPLETADO
> Resultado esperado: La app captura el documento con guia visual y deteccion de bordes. Rechaza capturas borrosas o mal alineadas antes de enviar al backend.
> Completado: DocumentCapture.tsx + DocumentGuide component + imageProcessing.ts utils.

---

## 5.5 Integracion con Backend

### Tareas

- [x] Implementar servicio API en el frontend:
  ```typescript
  class VerificationAPI {
    async startVerification(data: {
      selfieFrames: string[];    // base64 array
      documentImage: string;     // base64
      deviceFingerprint: string;
      challenges: ChallengeResult[];
    }): Promise<{ sessionId: string }>;

    async getStatus(sessionId: string): Promise<VerificationResult>;

    async pollResult(sessionId: string, intervalMs: number): Promise<VerificationResult>;
  }
  ```

- [x] Implementar polling o WebSocket para resultado en tiempo real.

- [x] Implementar manejo de errores:
  - Timeout (mostrar "Intenta de nuevo").
  - Error de red (mostrar "Sin conexion").
  - Rate limit (mostrar "Demasiados intentos, espera X minutos").

- [x] Implementar reintento inteligente:
  - Si rechazo por calidad de imagen → volver a captura con feedback especifico.
  - Si rechazo por liveness → volver a challenges.
  - Si rechazo definitivo → mostrar resultado final.

### Checkpoint 5.5 ✅ COMPLETADO
> Resultado esperado: La app envia datos al backend, muestra progreso y resultado. Reintentos funcionan correctamente.
> Completado: api.ts service + useVerification hook + ProcessingScreen polling + ResultScreen reintentos + ErrorScreen.

---

## 5.6 Version Web (WebRTC)

**Skills**: `webrtc_media_devices`

### Tareas

- [x] Implementar captura de selfie con WebRTC:
  - `navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })`.
  - Bloquear seleccion de archivo (no `<input type="file">`).
  - Misma logica de deteccion de rostro con MediaPipe.js.

- [x] Implementar captura de documento con WebRTC:
  - Camara trasera si disponible, frontal como fallback.
  - Overlay de guia.

- [x] Adaptar el flujo de UX para web (responsive).

### Checkpoint 5.6 ✅ COMPLETADO
> Resultado esperado: Version web funcional con captura de selfie y documento via WebRTC.
> Completado: React + Vite + React Router app con 6 paginas, WebRTC camera hook, API service, CSS responsive.

---

## Criterios de Completitud de Fase 5

- [x] App movil (React Native) con flujo completo de verificacion
- [x] Captura de selfie: solo camara en vivo, deteccion de rostro on-device
- [x] Captura de documento: overlay guia, deteccion de bordes, auto-captura
- [x] Challenges activos (parpadeo, giro) funcionan en la app
- [x] Integracion con backend funcional (envio, polling, resultado)
- [x] Manejo de errores y reintentos
- [x] Version web con WebRTC funcional
- [ ] UX validada con usuarios de prueba (Pendiente - requiere testing real)
