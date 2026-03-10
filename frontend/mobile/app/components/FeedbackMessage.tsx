import React from "react";
import { View, StyleSheet } from "react-native";
import { Text } from "react-native-paper";

interface Props {
  message: string;
}

export default function FeedbackMessage({ message }: Props) {
  return (
    <View style={styles.container} pointerEvents="none">
      <View style={styles.pill}>
        <Text variant="bodyMedium" style={styles.text}>
          {message}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    top: 60,
    left: 0,
    right: 0,
    alignItems: "center",
  },
  pill: {
    backgroundColor: "rgba(0, 0, 0, 0.7)",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 24,
  },
  text: {
    color: "#fff",
    textAlign: "center",
  },
});
