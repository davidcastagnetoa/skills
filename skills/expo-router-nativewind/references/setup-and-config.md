# Expo Router + NativeWind — Setup y Configuración

## Fuentes

- Expo Router: https://docs.expo.dev/router/installation/
- NativeWind v4: https://www.nativewind.dev/getting-started/expo-router

---

## 1. Creación del proyecto

```bash
npx create-expo-app apps/mobile --template blank-typescript
cd apps/mobile
```

---

## 2. Instalar dependencias principales

```bash
# Expo Router (navegación file-based)
npx expo install expo-router expo-linking expo-constants expo-status-bar

# NativeWind + Tailwind
npm install nativewind tailwindcss
npx tailwindcss init

# UI y utilidades
npx expo install expo-safe-area-context react-native-screens
npx expo install expo-image expo-haptics
npx expo install @expo/vector-icons

# Notificaciones
npx expo install expo-notifications expo-device

# Almacenamiento seguro (tokens JWT)
npx expo install expo-secure-store
```

---

## 3. Configuración babel.config.js

```javascript
// babel.config.js
module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ['babel-preset-expo', { jsxImportSource: 'nativewind' }],
    ],
    plugins: [
      'nativewind/babel',
    ],
  };
};
```

---

## 4. Configuración tailwind.config.js

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,jsx,ts,tsx}',
    './components/**/*.{js,jsx,ts,tsx}',
  ],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        // Paleta de colores HADA
        primary: {
          50:  '#fdf4ff',
          100: '#fae8ff',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
        },
        gift: {
          available: '#22c55e',   // Verde para disponible
          reserved: '#f59e0b',    // Ámbar para reservado
          received: '#6b7280',    // Gris para recibido
        },
      },
      fontFamily: {
        sans: ['Inter_400Regular', 'System'],
        medium: ['Inter_500Medium', 'System'],
        bold: ['Inter_700Bold', 'System'],
      },
    },
  },
  plugins: [],
};
```

---

## 5. app.json / app.config.ts

```typescript
// app.config.ts
import { ExpoConfig, ConfigContext } from 'expo/config';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: 'HADA',
  slug: 'hada-app',
  version: '1.0.0',
  scheme: 'hada',              // ← Scheme para deep links: hada://...
  orientation: 'portrait',
  icon: './assets/icon.png',
  userInterfaceStyle: 'light',
  splash: {
    image: './assets/splash.png',
    resizeMode: 'contain',
    backgroundColor: '#a855f7',
  },
  ios: {
    supportsTablet: false,
    bundleIdentifier: 'com.goldenhavenlabs.hada',
    infoPlist: {
      UIBackgroundModes: ['remote-notification'],
    },
  },
  android: {
    adaptiveIcon: { foregroundImage: './assets/adaptive-icon.png', backgroundColor: '#a855f7' },
    package: 'com.goldenhavenlabs.hada',
    googleServicesFile: './google-services.json',   // FCM en Android
    permissions: ['RECEIVE_BOOT_COMPLETED'],
  },
  plugins: [
    'expo-router',
    'expo-secure-store',
    ['expo-notifications', {
      icon: './assets/notification-icon.png',
      color: '#a855f7',
      sounds: [],
    }],
  ],
  experiments: { typedRoutes: true },
  extra: {
    API_BASE_URL: process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:3000',
    eas: { projectId: process.env.EAS_PROJECT_ID },
  },
});
```

---

## 6. Variables de entorno (.env)

```env
# .env.local (desarrollo)
EXPO_PUBLIC_API_URL=http://localhost:3000

# .env.production
EXPO_PUBLIC_API_URL=https://api.hada.app
```

> En Expo, solo las variables prefijadas con `EXPO_PUBLIC_` son accesibles en el cliente.
> Usar `process.env.EXPO_PUBLIC_API_URL` directamente en código.

---

## 7. Cliente HTTP (Axios + interceptores JWT)

```typescript
// lib/api.ts
import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { router } from 'expo-router';

export const api = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor: añadir accessToken a cada petición
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('accessToken');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Interceptor: refresh token automático en 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = await SecureStore.getItemAsync('refreshToken');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${process.env.EXPO_PUBLIC_API_URL}/auth/refresh`, { refreshToken });
          await SecureStore.setItemAsync('accessToken', data.accessToken);
          error.config.headers.Authorization = `Bearer ${data.accessToken}`;
          return api(error.config);
        } catch {
          await SecureStore.deleteItemAsync('accessToken');
          await SecureStore.deleteItemAsync('refreshToken');
          router.replace('/(auth)/login');
        }
      }
    }
    return Promise.reject(error);
  }
);
```
