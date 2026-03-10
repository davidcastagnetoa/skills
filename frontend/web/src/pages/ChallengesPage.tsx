import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { ChallengeResult } from "../types";

type ChallengeType = ChallengeResult["type"];

const CHALLENGES: ChallengeType[] = ["blink", "turn_right", "smile"];
const TIMEOUT_MS = 10_000;

const LABELS: Record<ChallengeType, { icon: string; text: string }> = {
  blink: { icon: "\uD83D\uDC41\uFE0F", text: "Parpadea naturalmente" },
  turn_left: { icon: "\u2B05\uFE0F", text: "Gira la cabeza a la izquierda" },
  turn_right: { icon: "\u27A1\uFE0F", text: "Gira la cabeza a la derecha" },
  smile: { icon: "\uD83D\uDE04", text: "Sonrie" },
};

export default function ChallengesPage() {
  const navigate = useNavigate();
  const [index, setIndex] = useState(0);
  const [results, setResults] = useState<ChallengeResult[]>([]);
  const [timeLeft, setTimeLeft] = useState(TIMEOUT_MS);

  const current = CHALLENGES[index];
  const label = LABELS[current];

  const completeChallenge = useCallback(
    (passed: boolean) => {
      const result: ChallengeResult = {
        type: current,
        passed,
        timestampMs: Date.now(),
      };
      const updated = [...results, result];
      setResults(updated);

      if (index + 1 < CHALLENGES.length) {
        setIndex((i) => i + 1);
        setTimeLeft(TIMEOUT_MS);
      } else {
        sessionStorage.setItem("challenges", JSON.stringify(updated));
        navigate("/document");
      }
    },
    [current, index, results, navigate]
  );

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 100) {
          completeChallenge(false);
          return TIMEOUT_MS;
        }
        return t - 100;
      });
    }, 100);
    return () => clearInterval(timer);
  }, [index, completeChallenge]);

  return (
    <div className="page">
      <h2 className="mb-16 text-center">
        Desafio {index + 1} de {CHALLENGES.length}
      </h2>

      <div
        style={{
          width: "100%",
          height: 6,
          background: "#e0e0e0",
          borderRadius: 3,
          marginBottom: 32,
        }}
      >
        <div
          style={{
            width: `${(index / CHALLENGES.length) * 100}%`,
            height: "100%",
            background: "#1a73e8",
            borderRadius: 3,
            transition: "width 0.3s",
          }}
        />
      </div>

      <div className="text-center mb-24">
        <span style={{ fontSize: 64 }}>{label.icon}</span>
        <h3 className="mb-8">{label.text}</h3>
        <p style={{ color: "#999" }}>{Math.ceil(timeLeft / 1000)}s restantes</p>
      </div>

      <button
        className="btn btn-primary"
        onClick={() => completeChallenge(true)}
      >
        Completado
      </button>
    </div>
  );
}
