---
name: webrtc_media_devices
description: Acceso a cámara en vivo desde web bloqueando galería — base del pipeline de captura
type: Protocol
priority: Esencial
mode: Self-hosted
---

# webrtc_media_devices

WebRTC y MediaDevices permiten capturar video en tiempo real desde la cámara, garantizando que la imagen es tomada en el momento y no subida desde galería.

## When to use

Usar en el frontend web para toda captura de selfie y video de liveness.

## Instructions

1. `navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })`
2. Forzar cámara frontal con `facingMode: { exact: 'user' }` en móvil.
3. Renderizar stream en `<video autoplay playsinline muted>`.
4. Capturar frames dibujando en `<canvas>` → `canvas.toBlob('image/jpeg', 0.95)`.
5. No incluir `<input type="file">` en el flujo de selfie.
6. Enviar frames al backend vía WebSocket para análisis en tiempo real.
7. Aplicar constraint de resolución mínima: `{ width: { min: 640 }, height: { min: 480 } }`.

## Notes

- En HTTPS es obligatorio; en localhost funciona sin TLS.
- getUserMedia no está disponible en iframes sin `allow="camera"`.
- Para React Native usar `react-native-vision-camera`.