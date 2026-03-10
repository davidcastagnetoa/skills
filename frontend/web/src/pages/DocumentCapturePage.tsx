import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useWebRTCCamera } from "../hooks/useWebRTCCamera";

export default function DocumentCapturePage() {
  const navigate = useNavigate();
  const { videoRef, isActive, error, startCamera, captureHighQuality } =
    useWebRTCCamera({ facingMode: "environment" });
  const [isCapturing, setIsCapturing] = useState(false);
  const [feedback, setFeedback] = useState(
    "Alinea tu documento dentro del marco"
  );

  useEffect(() => {
    startCamera();
  }, [startCamera]);

  const handleCapture = () => {
    setIsCapturing(true);
    setFeedback("Capturando...");
    const image = captureHighQuality();
    if (image) {
      sessionStorage.setItem("documentImage", image);
      navigate("/processing");
    } else {
      setFeedback("Error al capturar. Intenta de nuevo.");
      setIsCapturing(false);
    }
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
        <div className="doc-guide" />
        <div className="feedback-pill">{feedback}</div>
      </div>

      <p className="mb-16 text-center" style={{ color: "#999", fontSize: 13 }}>
        Usa la camara trasera si es posible. Evita reflejos.
      </p>

      <button
        className="btn btn-primary"
        onClick={handleCapture}
        disabled={!isActive || isCapturing}
      >
        {isCapturing ? "Procesando..." : "Capturar Documento"}
      </button>
    </div>
  );
}
