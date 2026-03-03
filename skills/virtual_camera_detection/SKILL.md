---
name: virtual_camera_detection
description: Detectar drivers de cámara virtual (OBS, ManyCam) por fingerprinting de dispositivo
type: Algorithm
priority: Esencial
mode: Self-hosted
---

# virtual_camera_detection

Las cámaras virtuales permiten inyectar video pregrabado o deepfakes en el flujo. Esta skill detecta su uso y rechaza la sesión.

## When to use

Ejecutar al inicio de la captura, antes de aceptar cualquier frame para análisis.

## Instructions

1. Enumerar dispositivos con `navigator.mediaDevices.enumerateDevices()`.
2. Comparar label del dispositivo contra lista negra: `['OBS Virtual Camera', 'ManyCam', 'XSplit', 'EpocCam', 'DroidCam']`.
3. Analizar estadísticas del stream WebRTC (`getStats()`): cámaras virtuales muestran frameRate artificialmente estable (exactamente 30.000 fps).
4. Verificar entropía del ruido de sensor: cámaras reales tienen ruido térmico; las virtuales no.
5. Si se detecta cámara virtual: rechazar sesión con código `VIRTUAL_CAMERA_DETECTED`.
6. Mantener la lista negra actualizable en Redis sin redeploy.

## Notes

- Librería JS: FingerprintJS open-source (https://github.com/fingerprintjs/fingerprintjs).
- Combinar con módulo de liveness para detección multicapa.