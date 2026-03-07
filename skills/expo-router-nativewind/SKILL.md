---
name: expo-router-nativewind
description: >
  Desarrollo de aplicaciones móviles con Expo SDK, Expo Router (navegación file-based)
  y NativeWind (Tailwind CSS en React Native) para producción. Usar PROACTIVAMENTE cuando
  se trabaje con pantallas, navegación, layouts, deep links, notificaciones push en Expo,
  estilos con NativeWind/Tailwind en RN, o cualquier tarea del frontend móvil del proyecto.
  Activar siempre que aparezcan las palabras clave: Expo, expo-router, NativeWind, Expo Router,
  Stack, Tabs, app/(tabs), _layout.tsx, useRouter, useLocalSearchParams, usePathname,
  expo-notifications, deep link, notificaciones push Expo, tailwind en React Native,
  className en RN, useSafeAreaInsets, SplashScreen, o cualquier pantalla de la app móvil HADA.
---

# Expo Router + NativeWind — App Móvil HADA

Guía completa para desarrollar la app móvil de HADA con Expo SDK, Expo Router
(navegación file-based al estilo Next.js) y NativeWind (clases Tailwind en React Native).
Orientada a usuarios no tecnológicos: UI clara, onboarding rápido, deep links funcionales.

## Referencias disponibles

Lee el archivo correspondiente según la tarea:

- `references/setup-and-config.md` — Instalación, estructura de carpetas, babel config, variables de entorno
- `references/routing-and-navigation.md` — Expo Router: layouts, Stack, Tabs, rutas dinámicas, deep links
- `references/nativewind-patterns.md` — NativeWind: configuración, clases frecuentes, componentes base
- `references/screens.md` — Pantallas principales de HADA: onboarding, listas, reservas, círculos
- `references/push-notifications.md` — Expo Notifications: permisos, tokens, manejo foreground/background

---

## Cuándo usar cada referencia

| Tarea                                                        | Referencia                  |
| ------------------------------------------------------------ | --------------------------- |
| Configurar el proyecto móvil por primera vez                 | `setup-and-config.md`       |
| Crear rutas, layouts, tabs o navegación entre pantallas      | `routing-and-navigation.md` |
| Estilizar componentes con clases Tailwind                    | `nativewind-patterns.md`    |
| Implementar pantallas de onboarding, listas, reservas        | `screens.md`                |
| Registrar token FCM, manejar notificaciones push, deep links | `push-notifications.md`     |

---

## Reglas críticas (siempre en contexto)

### 1. Expo Router: la estructura de carpetas ES la navegación

```
apps/mobile/app/
├── _layout.tsx              ← Root layout: providers, auth gate, SplashScreen
├── (auth)/
│   ├── _layout.tsx          ← Stack sin header ni tabs
│   ├── login.tsx
│   └── register.tsx
├── (app)/
│   ├── _layout.tsx          ← Tabs: Home, Círculos, Perfil
│   ├── index.tsx            ← Tab Home: listas del usuario
│   ├── circles/
│   │   ├── index.tsx        ← Lista de círculos
│   │   └── [id].tsx         ← Detalle círculo: rutas dinámicas /circles/:id
│   ├── lists/
│   │   ├── [id].tsx         ← Lista de deseos con regalos
│   │   └── [id]/
│   │       └── add-gift.tsx ← Añadir regalo a la lista
│   └── profile/
│       └── index.tsx
└── +not-found.tsx
```

### 2. NativeWind: usar `className` en componentes nativos, no `style`

```tsx
// ❌ Evitar StyleSheet cuando NativeWind está disponible
const styles = StyleSheet.create({ container: { padding: 16 } });
<View style={styles.container} />

// ✅ NativeWind con className
<View className="p-4 bg-white rounded-2xl shadow-sm" />
```

### 3. Deep links apuntan a rutas de Expo Router directamente

```
hada://lists/uuid-de-la-lista      →  app/(app)/lists/[id].tsx
hada://profiles/uuid/lists         →  app/(app)/profile/index.tsx
hada://circles/join?code=XXXX      →  app/(app)/circles/join.tsx
```

### 4. Tokens FCM se registran en el backend DESPUÉS del login exitoso

```tsx
const token = await registerForPushNotifications();
if (token) await api.post('/notifications/token', { token });
```

### 5. La privacidad del reservante se respeta en el frontend

```tsx
// ❌ Nunca mostrar quién reservó, aunque llegara del backend
<Text>{gift.reservation?.reservadoPor}</Text>

// ✅ Solo mostrar el estado visual
{gift.estado === 'RESERVED' && <Badge>Ya reservado 🔒</Badge>}
```

---

## Fuentes y documentación oficial

- **Expo Router Docs**: https://docs.expo.dev/router/introduction/
- **Expo Router Deep Linking**: https://docs.expo.dev/router/reference/url-parameters/
- **NativeWind v4 Docs**: https://www.nativewind.dev/
- **NativeWind + Expo Router Setup**: https://www.nativewind.dev/getting-started/expo-router
- **Expo Notifications**: https://docs.expo.dev/versions/latest/sdk/notifications/
- **Expo SDK Reference**: https://docs.expo.dev/versions/latest/
- **EAS Build**: https://docs.expo.dev/build/introduction/
- **Expo Config Plugins**: https://docs.expo.dev/config-plugins/introduction/
