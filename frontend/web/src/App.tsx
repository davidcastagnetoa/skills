import { Routes, Route } from "react-router-dom";
import WelcomePage from "./pages/WelcomePage";
import SelfieCapturePage from "./pages/SelfieCapturePage";
import ChallengesPage from "./pages/ChallengesPage";
import DocumentCapturePage from "./pages/DocumentCapturePage";
import ProcessingPage from "./pages/ProcessingPage";
import ResultPage from "./pages/ResultPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<WelcomePage />} />
      <Route path="/selfie" element={<SelfieCapturePage />} />
      <Route path="/challenges" element={<ChallengesPage />} />
      <Route path="/document" element={<DocumentCapturePage />} />
      <Route path="/processing" element={<ProcessingPage />} />
      <Route path="/result" element={<ResultPage />} />
    </Routes>
  );
}
