import React, { useCallback, useEffect, useState } from "react";
import { View, StyleSheet } from "react-native";
import { ActivityIndicator, Text } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { RootStackParamList, SessionProgress } from "../types";
import { verificationAPI } from "../services/api";
import { getDeviceFingerprint } from "../services/deviceFingerprint";
import ProgressIndicator from "../components/ProgressIndicator";

type Props = NativeStackScreenProps<RootStackParamList, "Processing">;

const POLL_INTERVAL_MS = 1500;
const MAX_POLL_ATTEMPTS = 40; // 60s max

const PHASE_LABELS: Record<string, string> = {
  capture_validation: "Validando captura",
  liveness: "Verificando vida",
  doc_processing: "Procesando documento",
  face_match: "Comparando rostros",
  ocr: "Extrayendo datos",
  antifraud: "Analisis antifraude",
  decision: "Generando decision",
};

export default function ProcessingScreen({ navigation, route }: Props) {
  const { selfieFrames, documentImage, challenges } = route.params;
  const [currentPhase, setCurrentPhase] = useState("Iniciando...");
  const [completedPhases, setCompletedPhases] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const startVerification = useCallback(async () => {
    try {
      const fingerprint = await getDeviceFingerprint();

      const { sessionId } = await verificationAPI.startVerification({
        selfieFrames,
        documentImage,
        deviceFingerprint: fingerprint,
        challenges,
      });

      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        try {
          const progress = await verificationAPI.getStatus(sessionId);

          setCurrentPhase(
            PHASE_LABELS[progress.currentPhase] ?? progress.currentPhase
          );
          setCompletedPhases(progress.completedPhases);

          if (progress.status === "completed" && progress.result) {
            clearInterval(poll);
            navigation.replace("Result", { result: progress.result });
          } else if (progress.status === "failed") {
            clearInterval(poll);
            setError("La verificacion ha fallado. Intenta de nuevo.");
          } else if (attempts >= MAX_POLL_ATTEMPTS) {
            clearInterval(poll);
            setError("Tiempo de espera agotado.");
          }
        } catch {
          clearInterval(poll);
          setError("Error de conexion.");
        }
      }, POLL_INTERVAL_MS);
    } catch (err) {
      setError("No se pudo iniciar la verificacion.");
    }
  }, [selfieFrames, documentImage, challenges, navigation]);

  useEffect(() => {
    startVerification();
  }, [startVerification]);

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.content}>
          <Text variant="headlineSmall" style={styles.errorText}>
            {error}
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <ActivityIndicator size="large" color="#1a73e8" />
        <Text variant="titleLarge" style={styles.title}>
          Verificando tu identidad
        </Text>
        <Text variant="bodyMedium" style={styles.phase}>
          {currentPhase}
        </Text>
        <ProgressIndicator
          completedPhases={completedPhases}
          phaseLabels={PHASE_LABELS}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  content: { flex: 1, justifyContent: "center", alignItems: "center", padding: 24 },
  title: { marginTop: 24, fontWeight: "bold", textAlign: "center" },
  phase: { marginTop: 8, color: "#666", textAlign: "center" },
  errorText: { color: "#d32f2f", textAlign: "center" },
});
