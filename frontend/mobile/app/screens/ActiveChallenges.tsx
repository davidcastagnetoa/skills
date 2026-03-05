import React, { useCallback, useEffect, useState } from "react";
import { View, StyleSheet } from "react-native";
import { Text, Button, ProgressBar } from "react-native-paper";
import { SafeAreaView } from "react-native-safe-area-context";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { RootStackParamList, ChallengeResult } from "../types";
import ChallengePrompt from "../components/ChallengePrompt";

type Props = NativeStackScreenProps<RootStackParamList, "ActiveChallenges">;

type ChallengeType = ChallengeResult["type"];

const CHALLENGE_SEQUENCE: ChallengeType[] = [
  "blink",
  "turn_right",
  "smile",
];
const TIMEOUT_MS = 10_000;

export default function ActiveChallengesScreen({ navigation, route }: Props) {
  const { selfieFrames } = route.params;
  const [currentIndex, setCurrentIndex] = useState(0);
  const [results, setResults] = useState<ChallengeResult[]>([]);
  const [timeLeft, setTimeLeft] = useState(TIMEOUT_MS);

  const currentChallenge = CHALLENGE_SEQUENCE[currentIndex];
  const progress = currentIndex / CHALLENGE_SEQUENCE.length;

  const handleChallengeComplete = useCallback(
    (passed: boolean) => {
      const result: ChallengeResult = {
        type: currentChallenge,
        passed,
        timestampMs: Date.now(),
      };
      const updated = [...results, result];
      setResults(updated);

      if (currentIndex + 1 < CHALLENGE_SEQUENCE.length) {
        setCurrentIndex((i) => i + 1);
        setTimeLeft(TIMEOUT_MS);
      } else {
        navigation.navigate("DocumentCapture", {
          selfieFrames,
          challenges: updated,
        });
      }
    },
    [currentChallenge, currentIndex, results, selfieFrames, navigation]
  );

  // Countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 100) {
          handleChallengeComplete(false); // timeout = fail
          return TIMEOUT_MS;
        }
        return t - 100;
      });
    }, 100);
    return () => clearInterval(timer);
  }, [currentIndex, handleChallengeComplete]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text variant="titleLarge" style={styles.title}>
          Desafio {currentIndex + 1} de {CHALLENGE_SEQUENCE.length}
        </Text>
        <ProgressBar
          progress={progress}
          color="#1a73e8"
          style={styles.progress}
        />
      </View>

      <View style={styles.content}>
        <ChallengePrompt type={currentChallenge} />
        <Text variant="bodySmall" style={styles.timer}>
          {Math.ceil(timeLeft / 1000)}s restantes
        </Text>
      </View>

      <View style={styles.controls}>
        <Button
          mode="contained"
          onPress={() => handleChallengeComplete(true)}
          style={styles.button}
        >
          Completado
        </Button>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f5f5f5" },
  header: { padding: 24 },
  title: { textAlign: "center", marginBottom: 12, fontWeight: "bold" },
  progress: { height: 6, borderRadius: 3 },
  content: { flex: 1, justifyContent: "center", alignItems: "center" },
  timer: { marginTop: 16, color: "#999" },
  controls: { padding: 24, alignItems: "center" },
  button: { borderRadius: 24, minWidth: 200 },
});
