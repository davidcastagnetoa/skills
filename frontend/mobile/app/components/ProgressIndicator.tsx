import React from "react";
import { View, StyleSheet } from "react-native";
import { Text } from "react-native-paper";

interface Props {
  completedPhases: string[];
  phaseLabels: Record<string, string>;
}

export default function ProgressIndicator({ completedPhases, phaseLabels }: Props) {
  const phases = Object.entries(phaseLabels);

  return (
    <View style={styles.container}>
      {phases.map(([key, label]) => {
        const done = completedPhases.includes(key);
        return (
          <View key={key} style={styles.row}>
            <Text style={[styles.icon, done && styles.iconDone]}>
              {done ? "\u2713" : "\u25CB"}
            </Text>
            <Text
              variant="bodySmall"
              style={[styles.label, done && styles.labelDone]}
            >
              {label}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 24,
    alignSelf: "stretch",
    paddingHorizontal: 48,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
  },
  icon: {
    fontSize: 16,
    width: 24,
    color: "#bbb",
  },
  iconDone: {
    color: "#4caf50",
  },
  label: {
    color: "#999",
  },
  labelDone: {
    color: "#333",
  },
});
