import { useRef, useState, useCallback, useEffect } from "react";
import { CameraView } from "expo-camera";

const DEFAULT_INTERVAL_MS = 200;
const DEFAULT_DURATION_MS = 4000;

interface UseCameraOptions {
  intervalMs?: number;
  durationMs?: number;
  quality?: number;
}

export function useCamera(options: UseCameraOptions = {}) {
  const {
    intervalMs = DEFAULT_INTERVAL_MS,
    durationMs = DEFAULT_DURATION_MS,
    quality = 0.7,
  } = options;

  const cameraRef = useRef<CameraView>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const maxFrames = Math.ceil(durationMs / intervalMs);

  const captureFrame = useCallback(async () => {
    if (!cameraRef.current) return null;
    const photo = await cameraRef.current.takePictureAsync({
      quality,
      base64: true,
      skipProcessing: true,
    });
    return photo?.base64 ?? null;
  }, [quality]);

  const captureSequence = useCallback(async (): Promise<string[]> => {
    return new Promise((resolve) => {
      setIsCapturing(true);
      const collected: string[] = [];

      intervalRef.current = setInterval(async () => {
        const frame = await captureFrame();
        if (frame) collected.push(frame);
        if (collected.length >= maxFrames) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          setIsCapturing(false);
          resolve(collected);
        }
      }, intervalMs);
    });
  }, [captureFrame, intervalMs, maxFrames]);

  const captureSingle = useCallback(async () => {
    if (!cameraRef.current) return null;
    const photo = await cameraRef.current.takePictureAsync({
      quality: 0.9,
      base64: true,
    });
    return photo?.base64 ?? null;
  }, []);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return { cameraRef, isCapturing, captureSequence, captureSingle };
}
