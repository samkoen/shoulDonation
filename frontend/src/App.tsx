import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { RequireSession } from "./components/RequireSession";
import { CustomerLeadsPage } from "./pages/CustomerLeadsPage";
import { DedicationPage } from "./pages/DedicationPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { ProjectPage } from "./pages/ProjectPage";
import { PublicProjectPage } from "./pages/public/PublicProjectPage";
import { SynagoguePage } from "./pages/SynagoguePage";
import { SessionProvider } from "./session/SessionProvider";

export function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/p/:slug" element={<PublicProjectPage />} />
          <Route element={<RequireSession />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/customers" element={<CustomerLeadsPage />} />
            <Route path="/synagogues/:synagogueId" element={<SynagoguePage />} />
            <Route path="/projects/:projectId" element={<ProjectPage />} />
            <Route path="/projects/:projectId/dedications/:dedicationId" element={<DedicationPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </SessionProvider>
  );
}
