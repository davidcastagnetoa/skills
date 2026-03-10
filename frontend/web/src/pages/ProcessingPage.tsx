import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { verificationAPI } from "../services/api";
import { ChallengeResult } from "../types";

const PHASE_LABELS: Record<string, string> = {
  capture_validation: "Validando captura",
  liveness: "Verificando vida",
  doc_processing: "Procesando documento",
  face_match: "Comparando rostros",
  ocr: "Extrayendo datos",
  antifraud: "Analisis antifraude",
  decision: "Generando decision",
};

function getFingerprint(): string {
  const raw = JSON.stringify({
    userAgent: navigator.userAgent,
    language: navigator.language,
    screen: `${screen.width}x${screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
  // Simple hash for web — not crypto-grade but sufficient for fingerprinting
  let hash = 0;
  for (let i = 0; i < raw.length; i++) {
    const chr = raw.charCodeAt(i);
    hash = (hash << 5) - hash + chr;
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padStart(8, "0");
}

export default function ProcessingPage() {
  const navigate = useNavigate();
  const [currentPhase, setCurrentPhase] = useState("Iniciando...");
  const [completedPhases, setCompletedPhases] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        const selfieFrames: string[] = JSON.parse(
          sessionStorage.getItem("selfieFrames") ?? "[]"
        );
        const challenges: ChallengeResult[] = JSON.parse(
          sessionStorage.getItem("challenges") ?? "[]"
        );
        const documentImage = sessionStorage.getItem("documentImage") ?? "";

        const { sessionId } = await verificationAPI.startVerification({
          selfieFrames,
          documentImage,
          deviceFingerprint: getFingerprint(),
          challenges,
        });

        let attempts = 0;
        const poll = setInterval(async () => {
          attempts++;
          try {
            const progress = await verificationAPI.getStatus(sessionId);
            setCurrentPhase(
              PHASE_LABELS[progress.currentPhase] ?? progress.currentPhase
            );
            setCompletedPhases(progress.completedPhases);

            if (progress.status === "completed" && progress.result) {
              clearInterval(poll);
              sessionStorage.setItem(
                "result",
                JSON.stringify(progress.result)
              );
              // Clean up captured data
              sessionStorage.removeItem("selfieFrames");
              sessionStorage.removeItem("challenges");
              sessionStorage.removeItem("documentImage");
              navigate("/result");
            } else if (progress.status === "failed") {
              clearInterval(poll);
              setError("La verificacion ha fallado.");
            } else if (attempts >= 40) {
              clearInterval(poll);
              setError("Tiempo de espera agotado.");
            }
          } catch {
            clearInterval(poll);
            setError("Error de conexion.");
          }
        }, 1500);
      } catch {
        setError("No se pudo iniciar la verificacion.");
      }
    };
    run();
  }, [navigate]);

  if (error) {
    return (
      <div className="page">
        <p style={{ color: "#d32f2f", fontSize: 18 }}>{error}</p>
        <button
          className="btn btn-primary"
          style={{ marginTop: 24 }}
          onClick={() => navigate("/")}
        >
          Volver al inicio
        </button>
      </div>
    );
  }

  return (
    <div className="page">
      <div
        style={{
          width: 48,
          height: 48,
          border: "4px solid #e0e0e0",
          borderTopColor: "#1a73e8",
          borderRadius: "50%",
          animation: "spin 1s linear infinite",
          marginBottom: 24,
        }}
      />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      <h2 className="mb-8 text-center">Verificando tu identidad</h2>
      <p className="mb-24 text-center" style={{ color: "#666" }}>
        {currentPhase}
      </p>

      <ul className="progress-list">
        {Object.entries(PHASE_LABELS).map(([key, label]) => {
          const done = completedPhases.includes(key);
          return (
            <li key={key} className={done ? "done" : ""}>
              <span className="check">{done ? "\u2713" : "\u25CB"}</span>
              {label}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
