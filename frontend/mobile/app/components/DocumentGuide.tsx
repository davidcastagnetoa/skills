import React from "react";
import { View, StyleSheet, Dimensions } from "react-native";
import { Text } from "react-native-paper";

const { width } = Dimensions.get("window");
const DOC_WIDTH = width * 0.85;
const DOC_HEIGHT = DOC_WIDTH * 0.63; // standard ID card ratio ~85.6x54mm

export default function DocumentGuide() {
  return (
    <View style={styles.container} pointerEvents="none">
      <View style={styles.frame}>
        {/* Corner markers */}
        <View style={[styles.corner, styles.topLeft]} />
        <View style={[styles.corner, styles.topRight]} />
        <View style={[styles.corner, styles.bottomLeft]} />
        <View style={[styles.corner, styles.bottomRight]} />
      </View>
      <Text variant="bodySmall" style={styles.hint}>
        Alinea el documento dentro del marco
      </Text>
    </View>
  );
}

const CORNER_SIZE = 24;
const CORNER_WIDTH = 3;

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: "center",
    alignItems: "center",
  },
  frame: {
    width: DOC_WIDTH,
    height: DOC_HEIGHT,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.4)",
    borderStyle: "dashed",
    borderRadius: 8,
  },
  hint: {
    color: "#fff",
    marginTop: 12,
    textAlign: "center",
  },
  corner: {
    position: "absolute",
    width: CORNER_SIZE,
    height: CORNER_SIZE,
  },
  topLeft: {
    top: -1,
    left: -1,
    borderTopWidth: CORNER_WIDTH,
    borderLeftWidth: CORNER_WIDTH,
    borderColor: "#1a73e8",
    borderTopLeftRadius: 8,
  },
  topRight: {
    top: -1,
    right: -1,
    borderTopWidth: CORNER_WIDTH,
    borderRightWidth: CORNER_WIDTH,
    borderColor: "#1a73e8",
    borderTopRightRadius: 8,
  },
  bottomLeft: {
    bottom: -1,
    left: -1,
    borderBottomWidth: CORNER_WIDTH,
    borderLeftWidth: CORNER_WIDTH,
    borderColor: "#1a73e8",
    borderBottomLeftRadius: 8,
  },
  bottomRight: {
    bottom: -1,
    right: -1,
    borderBottomWidth: CORNER_WIDTH,
    borderRightWidth: CORNER_WIDTH,
    borderColor: "#1a73e8",
    borderBottomRightRadius: 8,
  },
});
