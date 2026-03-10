import axios, { AxiosError } from "axios";
import {
  VerificationRequest,
  VerificationResult,
  SessionProgress,
} from "../types";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
const TIMEOUT_MS = 30_000;

const client = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: TIMEOUT_MS,
  headers: { "Content-Type": "application/json" },
});

export class VerificationAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = "VerificationAPIError";
  }
}

function handleError(err: unknown): never {
  if (err instanceof AxiosError) {
    const status = err.response?.status;
    if (status === 429) {
      throw new VerificationAPIError(
        "Demasiados intentos. Espera unos minutos.",
        429,
        true
      );
    }
    if (status && status >= 500) {
      throw new VerificationAPIError(
        "Error del servidor. Intenta de nuevo.",
        status,
        true
      );
    }
    if (!err.response) {
      throw new VerificationAPIError("Sin conexion a internet.", undefined, true);
    }
    throw new VerificationAPIError(
      err.response?.data?.detail ?? "Error desconocido.",
      status
    );
  }
  throw new VerificationAPIError("Error inesperado.");
}

class VerificationAPI {
  async startVerification(
    data: VerificationRequest
  ): Promise<{ sessionId: string }> {
    try {
      const response = await client.post("/verification/start", data);
      return { sessionId: response.data.session_id };
    } catch (err) {
      handleError(err);
    }
  }

  async getStatus(sessionId: string): Promise<SessionProgress> {
    try {
      const response = await client.get(`/verification/${sessionId}/status`);
      const d = response.data;
      return {
        sessionId: d.session_id,
        status: d.status,
        currentPhase: d.current_phase,
        completedPhases: d.completed_phases,
        result: d.result
          ? {
              sessionId: d.result.session_id,
              status: d.result.status,
              confidenceScore: d.result.confidence_score,
              reasons: d.result.reasons,
              processingTimeMs: d.result.processing_time_ms,
            }
          : undefined,
      };
    } catch (err) {
      handleError(err);
    }
  }

  async pollResult(
    sessionId: string,
    intervalMs: number = 1500,
    maxAttempts: number = 40
  ): Promise<VerificationResult> {
    return new Promise((resolve, reject) => {
      let attempts = 0;
      const timer = setInterval(async () => {
        attempts++;
        try {
          const progress = await this.getStatus(sessionId);
          if (progress.status === "completed" && progress.result) {
            clearInterval(timer);
            resolve(progress.result);
          } else if (progress.status === "failed") {
            clearInterval(timer);
            reject(new VerificationAPIError("Verificacion fallida."));
          } else if (attempts >= maxAttempts) {
            clearInterval(timer);
            reject(
              new VerificationAPIError("Tiempo de espera agotado.", undefined, true)
            );
          }
        } catch (err) {
          clearInterval(timer);
          reject(err);
        }
      }, intervalMs);
    });
  }
}

export const verificationAPI = new VerificationAPI();
