import { useRef, useState, useCallback, useEffect } from "react";

interface UseWebRTCCameraOptions {
  facingMode?: "user" | "environment";
}

export function useWebRTCCamera(options: UseWebRTCCameraOptions = {}) {
  const { facingMode = "user" } = options;
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode, width: { ideal: 1280 }, height: { ideal: 960 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsActive(true);
      setError(null);
    } catch (err) {
      setError("No se pudo acceder a la camara. Verifica los permisos.");
      setIsActive(false);
    }
  }, [facingMode]);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setIsActive(false);
  }, []);

  const captureFrame = useCallback((): string | null => {
    const video = videoRef.current;
    if (!video || !isActive) return null;

    if (!canvasRef.current) {
      canvasRef.current = document.createElement("canvas");
    }
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", 0.7).split(",")[1];
  }, [isActive]);

  const captureSequence = useCallback(
    (intervalMs = 200, durationMs = 4000): Promise<string[]> => {
      return new Promise((resolve) => {
        const frames: string[] = [];
        const maxFrames = Math.ceil(durationMs / intervalMs);
        const timer = setInterval(() => {
          const frame = captureFrame();
          if (frame) frames.push(frame);
          if (frames.length >= maxFrames) {
            clearInterval(timer);
            resolve(frames);
          }
        }, intervalMs);
      });
    },
    [captureFrame]
  );

  const captureHighQuality = useCallback((): string | null => {
    const video = videoRef.current;
    if (!video || !isActive) return null;

    if (!canvasRef.current) {
      canvasRef.current = document.createElement("canvas");
    }
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", 0.9).split(",")[1];
  }, [isActive]);

  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  return {
    videoRef,
    isActive,
    error,
    startCamera,
    stopCamera,
    captureFrame,
    captureSequence,
    captureHighQuality,
  };
}
