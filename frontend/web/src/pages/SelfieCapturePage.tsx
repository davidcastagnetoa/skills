import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useWebRTCCamera } from "../hooks/useWebRTCCamera";

export default function SelfieCapturePage() {
  const navigate = useNavigate();
  const { videoRef, isActive, error, startCamera, captureSequence } =
    useWebRTCCamera({ facingMode: "user" });
  const [isCapturing, setIsCapturing] = useState(false);
  const [feedback, setFeedback] = useState("Coloca tu rostro dentro del ovalo");

  useEffect(() => {
    startCamera();
  }, [startCamera]);

  const handleCapture = async () => {
    setIsCapturing(true);
    setFeedback("Mantente quieto...");
    const frames = await captureSequence();
    sessionStorage.setItem("selfieFrames", JSON.stringify(frames));
    navigate("/challenges");
  };

  if (error) {
    return (
      <div className="page">
        <p style={{ color: "#d32f2f" }}>{error}</p>
        <button className="btn btn-primary" onClick={startCamera}>
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="camera-container">
        <video ref={videoRef} autoPlay playsInline muted />
        <div className="face-oval" />
        <div className="feedback-pill">{feedback}</div>
      </div>

      <button
        className="btn btn-primary"
        onClick={handleCapture}
        disabled={!isActive || isCapturing}
      >
        {isCapturing ? "Capturando..." : "Capturar Selfie"}
      </button>
    </div>
  );
}
