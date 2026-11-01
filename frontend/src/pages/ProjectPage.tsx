import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getBudget, listDedications, listProjects, type Budget, type Dedication } from "../api";
import { BackLink } from "../components/BackLink";
import { Shell } from "../components/Shell";
import { BudgetEditor } from "./project/BudgetEditor";
import { CalculatorPanel } from "./project/CalculatorPanel";
import { DedicationCatalog, DedicationCreator } from "./project/DedicationBoard";
import { PriceSuggestion } from "./project/PriceSuggestion";
import { ProjectPlan } from "./project/ProjectPlan";
import { PublicPagePanel } from "./project/PublicPagePanel";
import { UnassignedLeads } from "./project/DonorLeads";
import { useRequiredSession } from "../session/SessionProvider";
import type { Project, Session } from "../session";

export function ProjectPage() {
  const { session } = useRequiredSession();
  const { projectId } = useParams();
  const [project, setProject] = useState<Project | null>(null);
  const [missing, setMissing] = useState(false);
  const [budget, setBudget] = useState<Budget | null>(null);
  const [dedications, setDedications] = useState<Dedication[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (projectId === undefined) {
      return;
    }
    void load(session, projectId, setProject, setMissing, setBudget, setDedications, setError);
  }, [session, projectId]);

  if (projectId === undefined) {
    return null;
  }

  const back = project && session.role === "platform_admin"
    ? { to: `/synagogues/${project.synagogueId}`, label: "לפרויקטים של בית הכנסת" }
    : { to: "/", label: "לכל הפרויקטים" };

  return (
    <Shell>
      <BackLink to={back.to} label={back.label} />
      {missing ? <MissingProject /> : null}
      {project ? <h1>{project.name}</h1> : null}
      {error ? <p className="error">{error}</p> : null}
      {project ? (
        <Workspace
          session={session}
          project={project}
          budget={budget}
          dedications={dedications}
          onChanged={() => void load(session, project.id, setProject, setMissing, setBudget, setDedications, setError)}
        />
      ) : null}
    </Shell>
  );
}

function MissingProject() {
  return (
    <p className="empty">
      הפרויקט לא נמצא. <Link to="/">חזרה</Link>
    </p>
  );
}

function Workspace({
  session,
  project,
  budget,
  dedications,
  onChanged,
}: {
  session: Session;
  project: Project;
  budget: Budget | null;
  dedications: Dedication[];
  onChanged: () => void;
}) {
  const canSetPrice = session.role !== "sub_projector";
  return (
    <div className="workspace">
      <BudgetCard budget={budget} />
      {canSetPrice ? <BudgetEditor session={session} projectId={project.id} onSaved={onChanged} /> : null}
      <ProjectPlan session={session} projectId={project.id} dedications={dedications} canReplace={canSetPrice} onChanged={onChanged} />
      <section className="workspace">
        <h2 className="section-title">הקדשות</h2>
        <p className="muted">כל הקדשה נפתחת לעמוד משלה: סטטוס, מחיר, מחשבון ולידים.</p>
        {canSetPrice ? (
          <div className="row">
            <DedicationCreator session={session} projectId={project.id} onCreated={onChanged} />
            <PriceSuggestion session={session} projectId={project.id} dedications={dedications} hasBudget={budget !== null} onApplied={onChanged} />
          </div>
        ) : null}
        <DedicationCatalog projectId={project.id} dedications={dedications} />
      </section>
      <CalculatorPanel session={session} projectId={project.id} canEditSettings={canSetPrice} />
      <UnassignedLeads session={session} projectId={project.id} dedications={dedications} />
      {canSetPrice ? <PublicPagePanel session={session} projectId={project.id} /> : null}
    </div>
  );
}

function BudgetCard({ budget }: { budget: Budget | null }) {
  if (budget === null) {
    return <article className="summary"><p>אין עדיין תקציב</p></article>;
  }
  return (
    <article className="summary">
      <p className="eyebrow">יעד הגיוס</p>
      <p className="amount">{budget.targetAmount} <small>{budget.currency}</small></p>
      <ProgressMeter total={budget.dedicationsTotal} target={budget.targetAmount} />
      <p className="muted">הקדשות {budget.dedicationsTotal} · פער {budget.gap}</p>
    </article>
  );
}

function ProgressMeter({ total, target }: { total: string; target: string }) {
  return (
    <div className="meter" aria-hidden="true">
      <span style={{ width: `${fillPercent(total, target)}%` }} />
    </div>
  );
}

function fillPercent(total: string, target: string): number {
  const goal = Number(target);
  if (!Number.isFinite(goal) || goal <= 0) {
    return 0;
  }
  return Math.min(100, Math.round((Number(total) / goal) * 100));
}

async function load(
  session: Session,
  projectId: string,
  setProject: (project: Project | null) => void,
  setMissing: (missing: boolean) => void,
  setBudget: (budget: Budget | null) => void,
  setDedications: (items: Dedication[]) => void,
  setError: (message: string) => void,
): Promise<void> {
  try {
    const projects = await listProjects(session);
    const project = projects.find((item) => item.id === projectId) ?? null;
    setProject(project);
    setMissing(project === null);
    setBudget(project ? await getBudget(session, project.id) : null);
    setDedications(project ? await listDedications(session, project.id) : []);
    setError("");
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
