import axios, { AxiosError } from "axios";
import { VerificationRequest, VerificationResult, SessionProgress } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "";

const client = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

export class VerificationAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public retryable = false
  ) {
    super(message);
  }
}

function handleError(err: unknown): never {
  if (err instanceof AxiosError) {
    const status = err.response?.status;
    if (status === 429)
      throw new VerificationAPIError("Demasiados intentos.", 429, true);
    if (status && status >= 500)
      throw new VerificationAPIError("Error del servidor.", status, true);
    if (!err.response)
      throw new VerificationAPIError("Sin conexion.", undefined, true);
    throw new VerificationAPIError(
      err.response.data?.detail ?? "Error desconocido.",
      status
    );
  }
  throw new VerificationAPIError("Error inesperado.");
}

class VerificationAPI {
  async startVerification(data: VerificationRequest): Promise<{ sessionId: string }> {
    try {
      const res = await client.post("/verification/start", data);
      return { sessionId: res.data.session_id };
    } catch (err) {
      handleError(err);
    }
  }

  async getStatus(sessionId: string): Promise<SessionProgress> {
    try {
      const res = await client.get(`/verification/${sessionId}/status`);
      const d = res.data;
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

  async pollResult(sessionId: string, intervalMs = 1500, maxAttempts = 40): Promise<VerificationResult> {
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
            reject(new VerificationAPIError("Tiempo agotado.", undefined, true));
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
