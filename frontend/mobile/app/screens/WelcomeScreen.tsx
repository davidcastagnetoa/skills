import React, { useCallback } from "react";
import { View, StyleSheet } from "react-native";
import { Button, Text, Surface } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { Camera } from "expo-camera";
import { RootStackParamList } from "../types";

type Props = NativeStackScreenProps<RootStackParamList, "Welcome">;

export default function WelcomeScreen({ navigation }: Props) {
  const handleStart = useCallback(async () => {
    const { status } = await Camera.requestCameraPermissionsAsync();
    if (status === "granted") {
      navigation.navigate("SelfieCapture");
    }
  }, [navigation]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text variant="headlineLarge" style={styles.title}>
          VerifID
        </Text>
        <Text variant="titleMedium" style={styles.subtitle}>
          Verificacion de Identidad
        </Text>

        <Surface style={styles.card} elevation={2}>
          <Text variant="bodyLarge" style={styles.step}>
            1. Toma una selfie en vivo
          </Text>
          <Text variant="bodyLarge" style={styles.step}>
            2. Completa los desafios de verificacion
          </Text>
          <Text variant="bodyLarge" style={styles.step}>
            3. Captura tu documento de identidad
          </Text>
          <Text variant="bodyLarge" style={styles.step}>
            4. Recibe el resultado al instante
          </Text>
        </Surface>

        <Text variant="bodySmall" style={styles.disclaimer}>
          Necesitaremos acceso a tu camara. Las imagenes se procesan de forma
          segura y se eliminan tras la verificacion.
        </Text>

        <Button
          mode="contained"
          onPress={handleStart}
          style={styles.button}
          contentStyle={styles.buttonContent}
        >
          Iniciar Verificacion
        </Button>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  content: { flex: 1, padding: 24, justifyContent: "center" },
  title: {
    textAlign: "center",
    fontWeight: "bold",
    color: "#1a73e8",
    marginBottom: 4,
  },
  subtitle: { textAlign: "center", color: "#666", marginBottom: 32 },
  card: { padding: 20, borderRadius: 12, marginBottom: 24 },
  step: { marginBottom: 12, paddingLeft: 8 },
  disclaimer: {
    textAlign: "center",
    color: "#999",
    marginBottom: 24,
    paddingHorizontal: 16,
  },
  button: { borderRadius: 8 },
  buttonContent: { paddingVertical: 8 },
});
