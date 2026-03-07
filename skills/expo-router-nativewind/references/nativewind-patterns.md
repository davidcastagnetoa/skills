# NativeWind — Patrones y Componentes Base HADA

## Fuente: https://www.nativewind.dev/

---

## 1. Configuración global.css (requerida en NativeWind v4)

```css
/* apps/mobile/global.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Importar en el root layout: `import '../global.css';`

---

## 2. Componentes base reutilizables

```tsx
// components/ui/Button.tsx
import { Pressable, Text, ActivityIndicator } from 'react-native';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
  disabled?: boolean;
}

export function Button({ title, onPress, variant = 'primary', loading, disabled }: ButtonProps) {
  const base = 'flex-row items-center justify-center rounded-2xl px-6 py-4 active:opacity-80';
  const variants = {
    primary: 'bg-primary-600',
    secondary: 'bg-white border border-gray-200',
    ghost: 'bg-transparent',
  };
  const textVariants = {
    primary: 'text-white font-medium text-base',
    secondary: 'text-gray-900 font-medium text-base',
    ghost: 'text-primary-600 font-medium text-base',
  };

  return (
    <Pressable
      className={`${base} ${variants[variant]} ${disabled || loading ? 'opacity-50' : ''}`}
      onPress={onPress}
      disabled={disabled || loading}
    >
      {loading && <ActivityIndicator size="small" color={variant === 'primary' ? 'white' : '#9333ea'} className="mr-2" />}
      <Text className={textVariants[variant]}>{title}</Text>
    </Pressable>
  );
}
```

```tsx
// components/ui/GiftCard.tsx — Tarjeta de regalo con badge de estado
import { View, Text, Image, Pressable } from 'react-native';

interface GiftCardProps {
  gift: { id: string; titulo: string; imagenUrl?: string; estado: string; precioEstimado?: number };
  onReserve?: () => void;
  canReserve?: boolean;
  isOwnList?: boolean;  // Propietario no puede reservar
}

export function GiftCard({ gift, onReserve, canReserve, isOwnList }: GiftCardProps) {
  const isAvailable = gift.estado === 'AVAILABLE';
  const isReserved = gift.estado === 'RESERVED';

  return (
    <View className="bg-white rounded-2xl p-4 mb-3 shadow-sm border border-gray-100">
      {gift.imagenUrl && (
        <Image source={{ uri: gift.imagenUrl }} className="w-full h-40 rounded-xl mb-3 bg-gray-100" />
      )}

      <Text className="text-base font-medium text-gray-900 mb-1">{gift.titulo}</Text>

      {gift.precioEstimado && (
        <Text className="text-sm text-gray-500 mb-3">~{gift.precioEstimado}€</Text>
      )}

      <View className="flex-row items-center justify-between">
        {/* Badge de estado — NUNCA revela quién reservó */}
        <View className={`px-3 py-1 rounded-full ${isAvailable ? 'bg-green-100' : isReserved ? 'bg-amber-100' : 'bg-gray-100'}`}>
          <Text className={`text-xs font-medium ${isAvailable ? 'text-green-700' : isReserved ? 'text-amber-700' : 'text-gray-600'}`}>
            {isAvailable ? '✓ Disponible' : isReserved ? '🔒 Reservado' : '✓ Recibido'}
          </Text>
        </View>

        {/* Botón "Lo compro yo" — solo para miembros del círculo, no para el propietario */}
        {isAvailable && canReserve && !isOwnList && (
          <Pressable
            onPress={onReserve}
            className="bg-primary-600 px-4 py-2 rounded-xl active:bg-primary-700"
          >
            <Text className="text-white text-sm font-medium">Lo compro yo</Text>
          </Pressable>
        )}
      </View>
    </View>
  );
}
```

---

## 3. Layout base con SafeArea

```tsx
// components/layout/Screen.tsx
import { View, ScrollView } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

interface ScreenProps {
  children: React.ReactNode;
  scroll?: boolean;
  className?: string;
}

export function Screen({ children, scroll, className = '' }: ScreenProps) {
  const insets = useSafeAreaInsets();

  const Container = scroll ? ScrollView : View;
  return (
    <Container
      className={`flex-1 bg-gray-50 ${className}`}
      style={{ paddingTop: insets.top }}
      contentContainerStyle={scroll ? { paddingBottom: insets.bottom + 16 } : undefined}
    >
      {children}
    </Container>
  );
}
```

---

## 4. Input con validación

```tsx
// components/ui/Input.tsx
import { View, Text, TextInput, TextInputProps } from 'react-native';

interface InputProps extends TextInputProps {
  label: string;
  error?: string;
}

export function Input({ label, error, ...props }: InputProps) {
  return (
    <View className="mb-4">
      <Text className="text-sm font-medium text-gray-700 mb-2">{label}</Text>
      <TextInput
        className={`bg-white border rounded-xl px-4 py-3 text-base text-gray-900
          ${error ? 'border-red-400' : 'border-gray-200'}`}
        placeholderTextColor="#9ca3af"
        {...props}
      />
      {error && <Text className="text-xs text-red-500 mt-1">{error}</Text>}
    </View>
  );
}
```

---

## 5. Clases Tailwind más usadas en HADA

```
Layouts:        flex-1, flex-row, items-center, justify-between, gap-3
Spacing:        p-4, px-6, py-3, mb-3, mt-4
Colores marca:  bg-primary-600, text-primary-600, border-primary-200
Cards:          bg-white rounded-2xl shadow-sm border border-gray-100 p-4
Textos:         text-2xl font-bold, text-base font-medium, text-sm text-gray-500
Estados gift:   bg-green-100 text-green-700, bg-amber-100 text-amber-700
Botones:        rounded-2xl px-6 py-4 active:opacity-80
```
