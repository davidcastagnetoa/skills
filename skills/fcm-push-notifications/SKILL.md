---
name: fcm-push-notifications
description: >
  Integración completa de Firebase Cloud Messaging (FCM) en backend NestJS y frontend
  Expo React Native. Usar PROACTIVAMENTE cuando se trabaje con notificaciones push,
  registro de tokens de dispositivo, envío de mensajes desde el servidor, manejo de
  tokens expirados o inválidos, notificaciones en foreground/background, deep links
  desde notificaciones, o configuración de credenciales FCM.
  Activar siempre que aparezcan las palabras clave: FCM, Firebase Cloud Messaging,
  push notification, getDevicePushTokenAsync, firebase-admin, sendEachForMulticast,
  fcmTokens, google-services.json, GoogleService-Info.plist, expo-notifications,
  notificación de cumpleaños, recordatorio push, o token de dispositivo.
---

# FCM Push Notifications — Backend NestJS + Expo React Native

Guía completa de integración de Firebase Cloud Messaging (FCM) para el sistema de
notificaciones push de HADA. Cubre backend (NestJS + firebase-admin) y cliente móvil
(Expo Notifications), incluyendo gestión de tokens, manejo de errores, deep links
y la conexión con el sistema de recordatorios.

## Referencias disponibles

- `references/backend-fcm.md` — Firebase Admin SDK en NestJS: inicialización, envío, manejo de errores
- `references/token-management.md` — Ciclo de vida de tokens FCM: registro, almacenamiento, limpieza
- `references/expo-client.md` — Lado cliente Expo: permisos, obtención de token nativo, listeners
- `references/deep-links.md` — Construir y procesar deep links en notificaciones HADA

---

## Cuándo usar cada referencia

| Tarea                                            | Referencia            |
| ------------------------------------------------ | --------------------- |
| Enviar notificaciones desde NestJS               | `backend-fcm.md`      |
| Registrar, actualizar o limpiar tokens FCM       | `token-management.md` |
| Configurar Expo para recibir notificaciones      | `expo-client.md`      |
| Crear deep links que abran pantallas específicas | `deep-links.md`       |

---

## Reglas críticas (siempre en contexto)

### 1. Inicializar Firebase Admin una sola vez

```typescript
if (!admin.apps.length) {
  admin.initializeApp({ credential: admin.credential.cert(serviceAccount) });
}
```

### 2. Usar `sendEachForMulticast` para múltiples tokens

```typescript
// ✅ Una sola llamada para N tokens
await admin.messaging().sendEachForMulticast({ tokens, notification });
```

### 3. Limpiar tokens inválidos después de cada envío

```typescript
response.responses.forEach((resp, idx) => {
  if (!resp.success && isInvalidTokenError(resp.error?.code)) {
    invalidTokens.push(tokens[idx]);
  }
});
await removeInvalidTokens(invalidTokens);
```

### 4. El campo `data` del payload solo acepta `Record<string, string>`

```typescript
// ✅ Todo convertido a string
data: { profileId: uuid, deepLink: 'hada://lists/uuid' }
```

### 5. Las notificaciones push solo funcionan en dispositivo físico

---

## Fuentes y documentación oficial

- **Firebase Admin SDK — Node.js**: https://firebase.google.com/docs/admin/setup
- **FCM Send Messages**: https://firebase.google.com/docs/cloud-messaging/send-message
- **FCM Multicast**: https://firebase.google.com/docs/cloud-messaging/send-message#send-messages-to-multiple-devices
- **FCM Error Codes**: https://firebase.google.com/docs/cloud-messaging/send-message#admin-error-codes
- **Expo Notifications Docs**: https://docs.expo.dev/versions/latest/sdk/notifications/
- **Expo + FCM Setup (Android)**: https://docs.expo.dev/push-notifications/fcm-credentials/
- **Expo + APNs Setup (iOS)**: https://docs.expo.dev/push-notifications/apns-credentials/
