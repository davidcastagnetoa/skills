import React from "react";
import { View, StyleSheet } from "react-native";
import { Text } from "react-native-paper";
import { ChallengeResult } from "../types";

type ChallengeType = ChallengeResult["type"];

const CHALLENGE_CONFIG: Record<ChallengeType, { icon: string; instruction: string }> = {
  blink: {
    icon: "\uD83D\uDC41\uFE0F",
    instruction: "Parpadea naturalmente",
  },
  turn_left: {
    icon: "\u2B05\uFE0F",
    instruction: "Gira la cabeza a la izquierda",
  },
  turn_right: {
    icon: "\u27A1\uFE0F",
    instruction: "Gira la cabeza a la derecha",
  },
  smile: {
    icon: "\uD83D\uDE04",
    instruction: "Sonrie",
  },
};

interface Props {
  type: ChallengeType;
}

export default function ChallengePrompt({ type }: Props) {
  const config = CHALLENGE_CONFIG[type];

  return (
    <View style={styles.container}>
      <Text style={styles.icon}>{config.icon}</Text>
      <Text variant="headlineSmall" style={styles.instruction}>
        {config.instruction}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    padding: 24,
  },
  icon: {
    fontSize: 64,
    marginBottom: 16,
  },
  instruction: {
    textAlign: "center",
    fontWeight: "bold",
  },
});
