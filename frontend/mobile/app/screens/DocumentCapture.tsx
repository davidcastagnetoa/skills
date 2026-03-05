import React, { useCallback, useRef, useState } from "react";
import { View, StyleSheet, Dimensions } from "react-native";
import { Text, Button } from "react-native-paper";
import { CameraView } from "expo-camera";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { RootStackParamList } from "../types";
import DocumentGuide from "../components/DocumentGuide";
import FeedbackMessage from "../components/FeedbackMessage";

type Props = NativeStackScreenProps<RootStackParamList, "DocumentCapture">;

export default function DocumentCaptureScreen({ navigation, route }: Props) {
  const { selfieFrames, challenges } = route.params;
  const cameraRef = useRef<CameraView>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [feedback, setFeedback] = useState(
    "Alinea tu documento dentro del marco"
  );

  const captureDocument = useCallback(async () => {
    if (!cameraRef.current) return;
    setIsCapturing(true);
    setFeedback("Capturando...");

    const photo = await cameraRef.current.takePictureAsync({
      quality: 0.9,
      base64: true,
    });

    if (photo?.base64) {
      navigation.navigate("Processing", {
        selfieFrames,
        documentImage: photo.base64,
        challenges,
      });
    } else {
      setFeedback("Error al capturar. Intenta de nuevo.");
      setIsCapturing(false);
    }
  }, [cameraRef, selfieFrames, challenges, navigation]);

  return (
    <View style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={styles.camera}
        facing="back"
        autofocus="on"
      >
        <DocumentGuide />
        <FeedbackMessage message={feedback} />
      </CameraView>

      <View style={styles.controls}>
        <Text variant="bodySmall" style={styles.hint}>
          Usa la camara trasera. Evita reflejos.
        </Text>
        <Button
          mode="contained"
          onPress={captureDocument}
          disabled={isCapturing}
          loading={isCapturing}
          style={styles.button}
        >
          {isCapturing ? "Procesando..." : "Capturar Documento"}
        </Button>
      </View>
    </View>
  );
}

const { width } = Dimensions.get("window");

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  camera: { flex: 1 },
  controls: {
    position: "absolute",
    bottom: 40,
    left: 0,
    right: 0,
    alignItems: "center",
  },
  hint: { color: "#ccc", marginBottom: 12 },
  button: { borderRadius: 24, minWidth: 200 },
});
