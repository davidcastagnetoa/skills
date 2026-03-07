# Expo Router — Navegación y Layouts HADA

## Fuente: https://docs.expo.dev/router/layouts/

---

## 1. Root Layout — auth gate y providers

```tsx
// app/_layout.tsx
import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { SplashScreen } from 'expo-router';
import * as SecureStore from 'expo-secure-store';
import { useRouter, useSegments } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import '../global.css';  // NativeWind CSS

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient();

function AuthGate() {
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    async function checkAuth() {
      const token = await SecureStore.getItemAsync('accessToken');
      const inAuthGroup = segments[0] === '(auth)';

      if (!token && !inAuthGroup) {
        router.replace('/(auth)/login');
      } else if (token && inAuthGroup) {
        router.replace('/(app)');
      }

      SplashScreen.hideAsync();
    }
    checkAuth();
  }, [segments]);

  return null;
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthGate />
      <Stack screenOptions={{ headerShown: false }} />
    </QueryClientProvider>
  );
}
```

---

## 2. Auth Layout (Stack sin tabs)

```tsx
// app/(auth)/_layout.tsx
import { Stack } from 'expo-router';

export default function AuthLayout() {
  return (
    <Stack>
      <Stack.Screen name="login" options={{ title: 'Iniciar sesión', headerShown: false }} />
      <Stack.Screen name="register" options={{ title: 'Crear cuenta', headerShown: false }} />
    </Stack>
  );
}
```

---

## 3. App Layout (Tabs principales)

```tsx
// app/(app)/_layout.tsx
import { Tabs } from 'expo-router';
import { Gift, Users, User } from 'lucide-react-native';

export default function AppLayout() {
  return (
    <Tabs screenOptions={{
      tabBarActiveTintColor: '#9333ea',
      tabBarInactiveTintColor: '#6b7280',
      tabBarStyle: { borderTopColor: '#f3f4f6' },
      headerShown: false,
    }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Mis Listas',
          tabBarIcon: ({ color, size }) => <Gift size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="circles"
        options={{
          title: 'Círculos',
          tabBarIcon: ({ color, size }) => <Users size={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Perfil',
          tabBarIcon: ({ color, size }) => <User size={size} color={color} />,
        }}
      />
    </Tabs>
  );
}
```

---

## 4. Rutas dinámicas y navegación programática

```tsx
// Navegar a una lista específica
import { router, Link } from 'expo-router';

// Imperativa
router.push(`/(app)/lists/${listId}`);
router.replace('/(auth)/login');  // Sin historial (logout)

// Declarativa
<Link href={`/(app)/lists/${listId}`} asChild>
  <Pressable><Text>Ver lista</Text></Pressable>
</Link>

// Leer parámetros de ruta dinámica en app/(app)/lists/[id].tsx
import { useLocalSearchParams } from 'expo-router';
const { id } = useLocalSearchParams<{ id: string }>();
```

---

## 5. Deep links desde notificaciones push

```tsx
// Al recibir notificación con deep link:
// Payload FCM: { deepLink: "hada://lists/uuid-123" }

// En el Root Layout, configurar el listener:
import * as Notifications from 'expo-notifications';

useEffect(() => {
  const subscription = Notifications.addNotificationResponseReceivedListener((response) => {
    const deepLink = response.notification.request.content.data?.deepLink as string;
    if (deepLink) {
      // Expo Router maneja automáticamente el scheme "hada://"
      router.push(deepLink.replace('hada:/', ''));
      // "hada://lists/uuid" → router.push("/(app)/lists/uuid")
    }
  });
  return () => subscription.remove();
}, []);
```

---

## 6. Pantalla de unirse a círculo via enlace de invitación

```tsx
// app/(app)/circles/join.tsx
// URL: hada://circles/join?code=ABC123
import { useLocalSearchParams, router } from 'expo-router';
import { api } from '../../../lib/api';

export default function JoinCircleScreen() {
  const { code } = useLocalSearchParams<{ code: string }>();

  async function handleJoin() {
    await api.post('/circles/join', { inviteCode: code });
    router.replace('/(app)/circles');
  }

  return (
    <View className="flex-1 items-center justify-center p-6">
      <Text className="text-2xl font-bold mb-4">Únete al círculo</Text>
      <Button onPress={handleJoin} title="Aceptar invitación" />
    </View>
  );
}
```
