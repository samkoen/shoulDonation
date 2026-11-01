import { FormEvent, useEffect, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { createProject, createSynagogue, listProjects, listSynagogues } from "../api";
import { Shell } from "../components/Shell";
import { useRequiredSession } from "../session/SessionProvider";
import type { Project, Session, Synagogue } from "../session";

export function HomePage() {
  const { session } = useRequiredSession();
  if (session.role === "platform_admin") {
    return <SynagogueHome session={session} />;
  }
  return <ProjectHome session={session} />;
}

function SynagogueHome({ session }: { session: Session }) {
  const [synagogues, setSynagogues] = useState<Synagogue[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void loadSynagogues(session, setSynagogues, setError);
  }, [session]);

  return (
    <Shell>
      <header className="page-head">
        <div>
          <p className="eyebrow">התחלה</p>
          <h1>בתי הכנסת</h1>
        </div>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <Link className="action-link" to="/customers">פניות לבית כנסת חדש</Link>
      <SynagogueForm session={session} onCreated={() => void loadSynagogues(session, setSynagogues, setError)} />
      <CardGrid empty="אין עדיין בתי כנסת">
        {synagogues.map((synagogue) => (
          <Link key={synagogue.id} className="card" to={`/synagogues/${synagogue.id}`}>
            <span className="eyebrow">בית כנסת</span>
            <strong>{synagogue.name}</strong>
            <span>לפרויקטים</span>
          </Link>
        ))}
      </CardGrid>
    </Shell>
  );
}

function ProjectHome({ session }: { session: Session }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");
  const canCreate = session.role === "lead_projector" && session.synagogueId !== null;

  useEffect(() => {
    void loadProjects(session, setProjects, setError);
  }, [session]);

  return (
    <Shell>
      <header className="page-head">
        <div>
          <p className="eyebrow">התחלה</p>
          <h1>הפרויקטים</h1>
        </div>
      </header>
      {error ? <p className="error">{error}</p> : null}
      {canCreate && session.synagogueId ? (
        <ProjectForm
          session={session}
          synagogueId={session.synagogueId}
          onCreated={() => void loadProjects(session, setProjects, setError)}
        />
      ) : null}
      <ProjectCards projects={projects} />
    </Shell>
  );
}

function ProjectCards({ projects }: { projects: Project[] }) {
  return (
    <CardGrid empty="אין עדיין פרויקטים">
      {projects.map((project) => (
        <Link key={project.id} className="card" to={`/projects/${project.id}`}>
          <span className="eyebrow">פרויקט</span>
          <strong>{project.name}</strong>
          <span>לתקציב ולהקדשות</span>
        </Link>
      ))}
    </CardGrid>
  );
}

function CardGrid({ children, empty }: { children: ReactNode; empty: string }) {
  const items = Array.isArray(children) ? children : [children];
  if (items.length === 0) {
    return <p className="empty">{empty}</p>;
  }
  return <div className="grid">{children}</div>;
}

async function loadSynagogues(
  session: Session,
  setSynagogues: (items: Synagogue[]) => void,
  setError: (message: string) => void,
): Promise<void> {
  try {
    setSynagogues(await listSynagogues(session));
    setError("");
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}

async function loadProjects(
  session: Session,
  setProjects: (items: Project[]) => void,
  setError: (message: string) => void,
): Promise<void> {
  try {
    setProjects(await listProjects(session));
    setError("");
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}

function SynagogueForm({ session, onCreated }: { session: Session; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await createSynagogue(session, name);
      setName("");
      setError("");
      setOpen(false);
      onCreated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  if (!open) {
    return <button type="button" onClick={() => setOpen(true)}>בית כנסת חדש</button>;
  }

  return (
    <form className="panel" onSubmit={submit}>
      <label>
        שם בית הכנסת
        <input value={name} onChange={(event) => setName(event.target.value)} required />
      </label>
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="submit">שמירה</button>
        <button type="button" className="ghost" onClick={() => setOpen(false)}>ביטול</button>
      </div>
    </form>
  );
}

export function ProjectForm({
  session,
  synagogueId,
  onCreated,
}: {
  session: Session;
  synagogueId: string;
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await createProject(session, synagogueId, name);
      setName("");
      setError("");
      setOpen(false);
      onCreated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  if (!open) {
    return <button type="button" onClick={() => setOpen(true)}>פרויקט חדש</button>;
  }

  return (
    <form className="panel" onSubmit={submit}>
      <label>
        שם הפרויקט
        <input value={name} onChange={(event) => setName(event.target.value)} required />
      </label>
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="submit">שמירה</button>
        <button type="button" className="ghost" onClick={() => setOpen(false)}>ביטול</button>
      </div>
    </form>
  );
}
