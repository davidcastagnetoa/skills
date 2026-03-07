# Expo Notifications — Push Notifications y Deep Links

## Fuente: https://docs.expo.dev/versions/latest/sdk/notifications/

---

## 1. Permisos y obtención del token

```tsx
// lib/notifications.ts
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Configurar comportamiento de notificaciones en foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export async function registerForPushNotifications(): Promise<string | null> {
  // Las notificaciones push solo funcionan en dispositivo físico
  if (!Device.isDevice) {
    console.warn('Push notifications require a physical device');
    return null;
  }

  // Pedir permisos
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.warn('Push notification permission denied');
    return null;
  }

  // Obtener token FCM (Expo Notifications usa FCM internamente en Android)
  try {
    const projectId = Constants.expoConfig?.extra?.eas?.projectId;
    const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;

    // En Android, crear canal de notificaciones
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('hada-reminders', {
        name: 'Recordatorios HADA',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#a855f7',
      });
    }

    return token;
  } catch (error) {
    console.error('Error getting push token:', error);
    return null;
  }
}
```

---

## 2. Registro del token en el backend (post-login)

```tsx
// hooks/useRegisterPushToken.ts
import { useEffect } from 'react';
import { registerForPushNotifications } from '../lib/notifications';
import { api } from '../lib/api';

export function useRegisterPushToken() {
  useEffect(() => {
    async function register() {
      const token = await registerForPushNotifications();
      if (token) {
        try {
          await api.post('/notifications/token', { token });
        } catch (error) {
          console.error('Failed to register push token:', error);
        }
      }
    }
    register();
  }, []);
}

// Uso en el layout autenticado:
// app/(app)/_layout.tsx
// useRegisterPushToken(); ← llamar aquí, una sola vez
```

---

## 3. Listener de notificaciones en el Root Layout

```tsx
// En app/_layout.tsx, dentro del componente principal:
import * as Notifications from 'expo-notifications';
import { router } from 'expo-router';
import { useEffect, useRef } from 'react';

function NotificationHandler() {
  const notificationListener = useRef<Notifications.Subscription>();
  const responseListener = useRef<Notifications.Subscription>();

  useEffect(() => {
    // Notificación recibida con la app ABIERTA (foreground)
    notificationListener.current = Notifications.addNotificationReceivedListener(notification => {
      console.log('Notification received in foreground:', notification.request.content.title);
      // Mostrar un banner in-app si se desea
    });

    // Usuario TAP en la notificación (app en background o cerrada)
    responseListener.current = Notifications.addNotificationResponseReceivedListener(response => {
      const data = response.notification.request.content.data;
      const deepLink = data?.deepLink as string | undefined;

      if (deepLink) {
        // Convierte "hada://lists/uuid" → "/(app)/lists/uuid"
        const path = deepLink.replace('hada:/', '');
        router.push(path as any);
      }
    });

    return () => {
      notificationListener.current?.remove();
      responseListener.current?.remove();
    };
  }, []);

  return null;
}
```

---

## 4. Diferencias Expo Push Token vs FCM Token

|         | Expo Push Token                             | FCM Token nativo                   |
| ------- | ------------------------------------------- | ---------------------------------- |
| Formato | `ExponentPushToken[xxx]`                    | Token largo de FCM                 |
| Uso     | Expo Push Service (desarrollo, testing)     | Firebase directamente (producción) |
| Backend | `POST https://exp.host/--/api/v2/push/send` | Firebase Admin SDK                 |
| HADA    | Desarrollo local                            | Producción via `firebase-admin`    |

> Para producción, el backend de HADA usa Firebase Admin SDK directamente.
> El token que se registra via `/notifications/token` debe ser el FCM nativo.
> Expo gestiona la conversión internamente si se usa EAS Build con las credenciales configuradas.

---

## 5. Manejo de notificaciones con app cerrada (cold start)

```tsx
// app/_layout.tsx — verificar si la app fue abierta desde una notificación
import * as Notifications from 'expo-notifications';

useEffect(() => {
  async function handleInitialNotification() {
    const response = await Notifications.getLastNotificationResponseAsync();
    if (response) {
      const deepLink = response.notification.request.content.data?.deepLink as string;
      if (deepLink) {
        // Pequeño delay para que el router esté listo
        setTimeout(() => {
          router.push(deepLink.replace('hada:/', '') as any);
        }, 500);
      }
    }
  }
  handleInitialNotification();
}, []);
```
