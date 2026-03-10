import { useState, useCallback } from "react";

export interface FaceDetectionState {
  faceDetected: boolean;
  faceCount: number;
  isWithinOval: boolean;
  feedback: string;
}

const INITIAL_STATE: FaceDetectionState = {
  faceDetected: false,
  faceCount: 0,
  isWithinOval: false,
  feedback: "Buscando rostro...",
};

/**
 * Hook for on-device face detection.
 * Currently provides a stub API — real ML detection (MediaPipe/MLKit)
 * will be integrated when native modules are configured.
 */
export function useFaceDetection() {
  const [state, setState] = useState<FaceDetectionState>(INITIAL_STATE);

  const onFacesDetected = useCallback(
    (faces: Array<{ bounds: { origin: { x: number; y: number }; size: { width: number; height: number } } }>) => {
      if (faces.length === 0) {
        setState({
          faceDetected: false,
          faceCount: 0,
          isWithinOval: false,
          feedback: "No se detecta ningun rostro",
        });
        return;
      }

      if (faces.length > 1) {
        setState({
          faceDetected: true,
          faceCount: faces.length,
          isWithinOval: false,
          feedback: "Solo debe haber un rostro en la imagen",
        });
        return;
      }

      const face = faces[0];
      const faceArea = face.bounds.size.width * face.bounds.size.height;
      const isLargeEnough = faceArea > 10000;

      setState({
        faceDetected: true,
        faceCount: 1,
        isWithinOval: isLargeEnough,
        feedback: isLargeEnough
          ? "Rostro detectado correctamente"
          : "Acerca tu rostro a la camara",
      });
    },
    []
  );

  const reset = useCallback(() => setState(INITIAL_STATE), []);

  return { ...state, onFacesDetected, reset };
}
