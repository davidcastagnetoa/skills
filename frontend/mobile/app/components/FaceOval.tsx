import React from "react";
import { View, StyleSheet, Dimensions } from "react-native";

const { width, height } = Dimensions.get("window");
const OVAL_WIDTH = width * 0.65;
const OVAL_HEIGHT = OVAL_WIDTH * 1.35;

export default function FaceOval() {
  return (
    <View style={styles.container} pointerEvents="none">
      <View style={styles.overlay}>
        <View style={styles.oval} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: "center",
    alignItems: "center",
  },
  overlay: {
    justifyContent: "center",
    alignItems: "center",
  },
  oval: {
    width: OVAL_WIDTH,
    height: OVAL_HEIGHT,
    borderRadius: OVAL_WIDTH / 2,
    borderWidth: 3,
    borderColor: "#1a73e8",
    borderStyle: "dashed",
    backgroundColor: "transparent",
  },
});
