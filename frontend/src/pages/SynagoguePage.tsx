import { useEffect, useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { listProjects, listSynagogues } from "../api";
import { BackLink } from "../components/BackLink";
import { Shell } from "../components/Shell";
import { ProjectForm } from "./HomePage";
import { useRequiredSession } from "../session/SessionProvider";
import type { Project, Session, Synagogue } from "../session";

export function SynagoguePage() {
  const { session } = useRequiredSession();
  const { synagogueId } = useParams();
  if (session.role !== "platform_admin" || synagogueId === undefined) {
    return <Navigate to="/" replace />;
  }
  return <SynagogueProjects session={session} synagogueId={synagogueId} />;
}

function SynagogueProjects({ session, synagogueId }: { session: Session; synagogueId: string }) {
  const [synagogue, setSynagogue] = useState<Synagogue | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void load(session, synagogueId, setSynagogue, setProjects, setError);
  }, [session, synagogueId]);

  return (
    <Shell>
      <BackLink to="/" label="לכל בתי הכנסת" />
      <header className="page-head">
        <div>
          <p className="eyebrow">בית כנסת</p>
          <h1>{synagogue?.name ?? "פרויקטים"}</h1>
        </div>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <ProjectForm session={session} synagogueId={synagogueId} onCreated={() => void load(session, synagogueId, setSynagogue, setProjects, setError)} />
      <div className="grid">
        {projects.map((project) => (
          <Link key={project.id} className="card" to={`/projects/${project.id}`}>
            <span className="eyebrow">פרויקט</span>
            <strong>{project.name}</strong>
            <span>לתקציב ולהקדשות</span>
          </Link>
        ))}
      </div>
      {projects.length === 0 ? <p className="empty">אין עדיין פרויקטים</p> : null}
    </Shell>
  );
}

async function load(
  session: Session,
  synagogueId: string,
  setSynagogue: (item: Synagogue | null) => void,
  setProjects: (items: Project[]) => void,
  setError: (message: string) => void,
): Promise<void> {
  try {
    const [synagogues, projects] = await Promise.all([listSynagogues(session), listProjects(session)]);
    setSynagogue(synagogues.find((item) => item.id === synagogueId) ?? null);
    setProjects(projects.filter((project) => project.synagogueId === synagogueId));
    setError("");
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
