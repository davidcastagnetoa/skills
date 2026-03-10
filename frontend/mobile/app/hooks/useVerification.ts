import { useState, useCallback } from "react";
import {
  VerificationRequest,
  VerificationResult,
  SessionProgress,
} from "../types";
import { verificationAPI, VerificationAPIError } from "../services/api";
import { getDeviceFingerprint } from "../services/deviceFingerprint";

type VerificationState = "idle" | "submitting" | "polling" | "done" | "error";

interface UseVerificationReturn {
  state: VerificationState;
  progress: SessionProgress | null;
  result: VerificationResult | null;
  error: string | null;
  canRetry: boolean;
  startVerification: (
    data: Omit<VerificationRequest, "deviceFingerprint">
  ) => Promise<void>;
  reset: () => void;
}

export function useVerification(): UseVerificationReturn {
  const [state, setState] = useState<VerificationState>("idle");
  const [progress, setProgress] = useState<SessionProgress | null>(null);
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [canRetry, setCanRetry] = useState(false);

  const reset = useCallback(() => {
    setState("idle");
    setProgress(null);
    setResult(null);
    setError(null);
    setCanRetry(false);
  }, []);

  const startVerification = useCallback(
    async (data: Omit<VerificationRequest, "deviceFingerprint">) => {
      try {
        setState("submitting");
        setError(null);

        const fingerprint = await getDeviceFingerprint();
        const { sessionId } = await verificationAPI.startVerification({
          ...data,
          deviceFingerprint: fingerprint,
        });

        setState("polling");
        const verificationResult = await verificationAPI.pollResult(sessionId);

        setResult(verificationResult);
        setState("done");
      } catch (err) {
        const message =
          err instanceof VerificationAPIError
            ? err.message
            : "Error inesperado.";
        const retryable =
          err instanceof VerificationAPIError ? err.retryable : false;

        setError(message);
        setCanRetry(retryable);
        setState("error");
      }
    },
    []
  );

  return { state, progress, result, error, canRetry, startVerification, reset };
}
