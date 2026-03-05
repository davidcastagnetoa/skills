import React, { useCallback, useEffect, useRef, useState } from "react";
import { View, StyleSheet, Dimensions } from "react-native";
import { Text, Button } from "react-native-paper";
import { CameraView, CameraType } from "expo-camera";
import { NativeStackScreenProps } from "@react-navigation/native-stack";
import { RootStackParamList } from "../types";
import FaceOval from "../components/FaceOval";
import FeedbackMessage from "../components/FeedbackMessage";

type Props = NativeStackScreenProps<RootStackParamList, "SelfieCapture">;

const CAPTURE_INTERVAL_MS = 200;
const CAPTURE_DURATION_MS = 4000;
const MAX_FRAMES = Math.ceil(CAPTURE_DURATION_MS / CAPTURE_INTERVAL_MS);

export default function SelfieCaptureScreen({ navigation }: Props) {
  const cameraRef = useRef<CameraView>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [frames, setFrames] = useState<string[]>([]);
  const [feedback, setFeedback] = useState("Coloca tu rostro dentro del ovalo");
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const captureFrame = useCallback(async () => {
    if (!cameraRef.current) return null;
    const photo = await cameraRef.current.takePictureAsync({
      quality: 0.7,
      base64: true,
      skipProcessing: true,
    });
    return photo?.base64 ?? null;
  }, []);

  const startCapture = useCallback(async () => {
    setIsCapturing(true);
    setFeedback("Mantente quieto...");
    const collected: string[] = [];

    intervalRef.current = setInterval(async () => {
      const frame = await captureFrame();
      if (frame) {
        collected.push(frame);
      }
      if (collected.length >= MAX_FRAMES) {
        if (intervalRef.current) clearInterval(intervalRef.current);
        setFrames(collected);
        setIsCapturing(false);
        navigation.navigate("ActiveChallenges", {
          selfieFrames: collected,
        });
      }
    }, CAPTURE_INTERVAL_MS);
  }, [captureFrame, navigation]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <View style={styles.container}>
      <CameraView
        ref={cameraRef}
        style={styles.camera}
        facing="front"
        mirror={true}
      >
        <FaceOval />
        <FeedbackMessage message={feedback} />
      </CameraView>

      <View style={styles.controls}>
        <Button
          mode="contained"
          onPress={startCapture}
          disabled={isCapturing}
          loading={isCapturing}
          style={styles.button}
        >
          {isCapturing ? "Capturando..." : "Capturar Selfie"}
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
  button: { borderRadius: 24, minWidth: 200 },
});
