import { useNavigate } from "react-router-dom";
import { VerificationResult } from "../types";

const STATUS_CONFIG = {
  VERIFIED: {
    icon: "\u2713",
    color: "#4caf50",
    title: "Identidad Verificada",
    subtitle: "Tu identidad ha sido verificada exitosamente.",
  },
  REJECTED: {
    icon: "\u2717",
    color: "#d32f2f",
    title: "Verificacion Rechazada",
    subtitle: "No se pudo verificar tu identidad.",
  },
  MANUAL_REVIEW: {
    icon: "\u231B",
    color: "#ff9800",
    title: "En Revision",
    subtitle: "Tu verificacion esta siendo revisada por un operador.",
  },
};

export default function ResultPage() {
  const navigate = useNavigate();
  const raw = sessionStorage.getItem("result");

  if (!raw) {
    return (
      <div className="page">
        <p>No hay resultado disponible.</p>
        <button className="btn btn-primary" onClick={() => navigate("/")}>
          Ir al inicio
        </button>
      </div>
    );
  }

  const result: VerificationResult = JSON.parse(raw);
  const config = STATUS_CONFIG[result.status];
  const canRetry =
    result.status === "REJECTED" &&
    result.reasons.some(
      (r) => r.includes("quality") || r.includes("blur") || r.includes("lighting")
    );

  return (
    <div className="page">
      <span className="status-icon" style={{ color: config.color }}>
        {config.icon}
      </span>
      <h2 className="mb-8 text-center">{config.title}</h2>
      <p className="mb-24 text-center" style={{ color: "#666" }}>
        {config.subtitle}
      </p>

      <div className="card">
        <p style={{ color: "#999", fontSize: 12, textTransform: "uppercase" }}>
          Confianza
        </p>
        <p style={{ fontSize: 24, fontWeight: "bold" }}>
          {(result.confidenceScore * 100).toFixed(1)}%
        </p>

        {result.reasons.length > 0 && (
          <>
            <p
              style={{
                color: "#999",
                fontSize: 12,
                textTransform: "uppercase",
                marginTop: 16,
              }}
            >
              Detalles
            </p>
            {result.reasons.map((reason, i) => (
              <p key={i} style={{ color: "#555", marginTop: 4 }}>
                {reason}
              </p>
            ))}
          </>
        )}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12, width: "100%" }}>
        {canRetry && (
          <button className="btn btn-primary" onClick={() => navigate("/selfie")}>
            Reintentar
          </button>
        )}
        <button
          className={canRetry ? "btn btn-outline" : "btn btn-primary"}
          onClick={() => {
            sessionStorage.removeItem("result");
            navigate("/");
          }}
        >
          Volver al inicio
        </button>
      </div>
    </div>
  );
}
