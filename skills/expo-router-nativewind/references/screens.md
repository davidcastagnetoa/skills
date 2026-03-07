# Expo Router — Pantallas Principales HADA

---

## 1. Onboarding / Register (< 60 segundos a primera lista)

```tsx
// app/(auth)/register.tsx
import { useState } from 'react';
import { View, Text, KeyboardAvoidingView, Platform } from 'react-native';
import { router } from 'expo-router';
import { api } from '../../lib/api';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import DateTimePicker from '@react-native-community/datetimepicker';
import * as SecureStore from 'expo-secure-store';

export default function RegisterScreen() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [birthday, setBirthday] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleRegister() {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/register', {
        nombre, email, password,
        birthdayDate: birthday?.toISOString(),
      });
      await SecureStore.setItemAsync('accessToken', data.accessToken);
      await SecureStore.setItemAsync('refreshToken', data.refreshToken);
      // Ir directo a crear primera lista
      router.replace('/(app)');
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-white"
    >
      <View className="flex-1 justify-center p-6">
        <Text className="text-3xl font-bold text-gray-900 mb-2">Crea tu cuenta</Text>
        <Text className="text-gray-500 mb-8">En menos de un minuto</Text>

        <Input label="Nombre" value={nombre} onChangeText={setNombre} placeholder="Tu nombre" />
        <Input label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
        <Input label="Contraseña" value={password} onChangeText={setPassword} secureTextEntry />

        <Text className="text-sm font-medium text-gray-700 mb-2">Tu cumpleaños</Text>
        {/* DatePicker nativo */}

        <Button title="Crear cuenta" onPress={handleRegister} loading={loading} className="mt-4" />

        <Button
          title="Ya tengo cuenta"
          variant="ghost"
          onPress={() => router.push('/(auth)/login')}
          className="mt-3"
        />
      </View>
    </KeyboardAvoidingView>
  );
}
```

---

## 2. Lista de deseos (pantalla principal del producto)

```tsx
// app/(app)/lists/[id].tsx
import { useLocalSearchParams } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { View, Text, FlatList, Alert } from 'react-native';
import { api } from '../../../lib/api';
import { GiftCard } from '../../../components/ui/GiftCard';
import { Screen } from '../../../components/layout/Screen';

export default function ListDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data: list, isLoading } = useQuery({
    queryKey: ['list', id],
    queryFn: () => api.get(`/lists/${id}`).then(r => r.data),
  });

  const reserveMutation = useMutation({
    mutationFn: (giftId: string) => api.post(`/gifts/${giftId}/reserve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['list', id] });
    },
    onError: () => Alert.alert('Error', 'No se pudo reservar. Inténtalo de nuevo.'),
  });

  if (isLoading) return <LoadingSkeleton />;

  return (
    <Screen scroll>
      <View className="px-4 pt-6 pb-4">
        <Text className="text-2xl font-bold text-gray-900">{list?.titulo}</Text>
        <Text className="text-gray-500 mt-1">Lista de {list?.ownerProfile?.nombre}</Text>
      </View>

      <FlatList
        data={list?.gifts}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View className="px-4">
            <GiftCard
              gift={item}
              canReserve={list?.canReserve}      // El backend indica si puede reservar
              isOwnList={list?.isOwnList}        // Propietario no puede reservar su propia lista
              onReserve={() => reserveMutation.mutate(item.id)}
            />
          </View>
        )}
        ListEmptyComponent={
          <View className="items-center py-16">
            <Text className="text-gray-400 text-base">Esta lista está vacía</Text>
          </View>
        }
        scrollEnabled={false}
      />
    </Screen>
  );
}
```

---

## 3. Home — listas accesibles del usuario

```tsx
// app/(app)/index.tsx
import { View, Text, FlatList, Pressable } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import { Screen } from '../../components/layout/Screen';
import { Plus } from 'lucide-react-native';

export default function HomeScreen() {
  const { data: lists } = useQuery({
    queryKey: ['lists'],
    queryFn: () => api.get('/lists').then(r => r.data),
  });

  return (
    <Screen scroll>
      <View className="flex-row items-center justify-between px-4 pt-6 pb-4">
        <Text className="text-2xl font-bold text-gray-900">Mis Listas</Text>
        <Pressable
          onPress={() => router.push('/(app)/lists/new')}
          className="bg-primary-600 p-3 rounded-full active:bg-primary-700"
        >
          <Plus size={20} color="white" />
        </Pressable>
      </View>

      <FlatList
        data={lists}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <Pressable
            className="mx-4 mb-3 bg-white rounded-2xl p-4 border border-gray-100 active:opacity-80"
            onPress={() => router.push(`/(app)/lists/${item.id}`)}
          >
            <Text className="font-medium text-gray-900">{item.titulo}</Text>
            <Text className="text-sm text-gray-500 mt-1">
              {item._count?.gifts ?? 0} regalos · {item.ownerProfile?.nombre}
            </Text>
          </Pressable>
        )}
        scrollEnabled={false}
      />
    </Screen>
  );
}
```

---

## 4. Loading skeleton reutilizable

```tsx
// components/ui/LoadingSkeleton.tsx
import { View } from 'react-native';

export function LoadingSkeleton() {
  return (
    <View className="flex-1 bg-gray-50 p-4">
      {[1, 2, 3].map((i) => (
        <View key={i} className="bg-white rounded-2xl p-4 mb-3 border border-gray-100">
          <View className="h-4 bg-gray-200 rounded w-3/4 mb-2 animate-pulse" />
          <View className="h-3 bg-gray-100 rounded w-1/2" />
        </View>
      ))}
    </View>
  );
}
```
