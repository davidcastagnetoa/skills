import { useNavigate } from "react-router-dom";

export default function WelcomePage() {
  const navigate = useNavigate();

  return (
    <div className="page">
      <h1 style={{ color: "#1a73e8", marginBottom: 4 }}>VerifID</h1>
      <p className="mb-24" style={{ color: "#666" }}>
        Verificacion de Identidad
      </p>

      <div className="card">
        <p className="mb-8">1. Toma una selfie en vivo</p>
        <p className="mb-8">2. Completa los desafios de verificacion</p>
        <p className="mb-8">3. Captura tu documento de identidad</p>
        <p>4. Recibe el resultado al instante</p>
      </div>

      <p className="mb-24 text-center" style={{ color: "#999", fontSize: 13 }}>
        Necesitaremos acceso a tu camara. Las imagenes se procesan de forma
        segura y se eliminan tras la verificacion.
      </p>

      <button className="btn btn-primary" onClick={() => navigate("/selfie")}>
        Iniciar Verificacion
      </button>
    </div>
  );
}
