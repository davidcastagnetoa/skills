import React, { ReactNode } from "react";
import { View, StyleSheet } from "react-native";

interface Props {
  children?: ReactNode;
}

export default function CameraOverlay({ children }: Props) {
  return (
    <View style={styles.container} pointerEvents="box-none">
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "transparent",
  },
});
