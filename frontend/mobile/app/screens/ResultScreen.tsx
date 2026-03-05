import React from "react";
import { View, StyleSheet } from "react-native";
import { Button, Text, Surface } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { RootStackParamList } from "../types";

type Props = NativeStackScreenProps<RootStackParamList, "Result">;

const STATUS_CONFIG = {
  VERIFIED: {
    icon: "\u2713",
    color: "#4caf50",
    title: "Identidad Verificada",
    subtitle: "Tu identidad ha sido verificada exitosamente.",
  },
  REJECTED: {
    icon: "\u2717",
    color: "#d32f2f",
    title: "Verificacion Rechazada",
    subtitle: "No se pudo verificar tu identidad.",
  },
  MANUAL_REVIEW: {
    icon: "\u231B",
    color: "#ff9800",
    title: "En Revision",
    subtitle: "Tu verificacion esta siendo revisada por un operador.",
  },
};

export default function ResultScreen({ navigation, route }: Props) {
  const { result } = route.params;
  const config = STATUS_CONFIG[result.status];

  const canRetry = result.status === "REJECTED" && result.reasons.some(
    (r) => r.includes("quality") || r.includes("blur") || r.includes("lighting")
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={[styles.icon, { color: config.color }]}>{config.icon}</Text>
        <Text variant="headlineMedium" style={styles.title}>
          {config.title}
        </Text>
        <Text variant="bodyLarge" style={styles.subtitle}>
          {config.subtitle}
        </Text>

        <Surface style={styles.card} elevation={1}>
          <Text variant="bodySmall" style={styles.label}>
            Confianza
          </Text>
          <Text variant="titleLarge" style={styles.score}>
            {(result.confidenceScore * 100).toFixed(1)}%
          </Text>

          {result.reasons.length > 0 && (
            <>
              <Text variant="bodySmall" style={[styles.label, { marginTop: 16 }]}>
                Detalles
              </Text>
              {result.reasons.map((reason, i) => (
                <Text key={i} variant="bodyMedium" style={styles.reason}>
                  {reason}
                </Text>
              ))}
            </>
          )}
        </Surface>

        <View style={styles.buttons}>
          {canRetry && (
            <Button
              mode="contained"
              onPress={() => navigation.navigate("SelfieCapture")}
              style={styles.button}
            >
              Reintentar
            </Button>
          )}
          <Button
            mode={canRetry ? "outlined" : "contained"}
            onPress={() => navigation.navigate("Welcome")}
            style={styles.button}
          >
            Volver al inicio
          </Button>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  content: { flex: 1, padding: 24, justifyContent: "center" },
  icon: { fontSize: 64, textAlign: "center", marginBottom: 16 },
  title: { textAlign: "center", fontWeight: "bold", marginBottom: 8 },
  subtitle: { textAlign: "center", color: "#666", marginBottom: 24 },
  card: { padding: 20, borderRadius: 12, marginBottom: 24 },
  label: { color: "#999", textTransform: "uppercase", letterSpacing: 1 },
  score: { fontWeight: "bold", color: "#333" },
  reason: { marginTop: 4, color: "#555" },
  buttons: { gap: 12 },
  button: { borderRadius: 8 },
});
