# FCM — Deep Links en Notificaciones HADA

## Tabla de deep links del proyecto

| Evento                     | Deep link                   | Pantalla Expo Router  |
| -------------------------- | --------------------------- | --------------------- |
| Cumpleaños próximo         | `hada://lists/{listId}`     | `/(app)/lists/[id]`   |
| Bienvenida a círculo       | `hada://circles/{circleId}` | `/(app)/circles/[id]` |
| Regalo reservado (miembro) | `hada://lists/{listId}`     | `/(app)/lists/[id]`   |

## Construcción del payload con deep link (backend)

```typescript
// En RemindersProcessor al construir la notificación:
await this.fcmService.send({
  tokens,
  title: `🎁 Cumpleaños de ${profileNombre}`,
  body: `El cumpleaños es en ${daysUntil} días`,
  data: {
    type: 'birthday_reminder',
    profileId,
    deepLink: `hada://lists/${primaryListId}`,  // ← Siempre string
  },
});
```

## Procesado en el cliente Expo

```tsx
// app/_layout.tsx
Notifications.addNotificationResponseReceivedListener((response) => {
  const deepLink = response.notification.request.content.data?.deepLink as string;
  if (deepLink) {
    // "hada://lists/uuid" → router.push("/(app)/lists/uuid")
    const path = deepLink.replace('hada:/', '');
    router.push(path as any);
  }
});
```
