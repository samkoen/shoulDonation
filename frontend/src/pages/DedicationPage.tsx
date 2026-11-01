import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { listDedications, listProjects, type Dedication } from "../api";
import { BackLink } from "../components/BackLink";
import { Shell } from "../components/Shell";
import { useRequiredSession } from "../session/SessionProvider";
import type { Session } from "../session";
import { CalculatorPanel } from "./project/CalculatorPanel";
import { DedicationActions } from "./project/DedicationBoard";
import { ContractorCard } from "./project/ContractorCard";
import { DedicationPlacement } from "./project/DedicationPlacement";
import { DonorLeads } from "./project/DonorLeads";

export function DedicationPage() {
  const { session } = useRequiredSession();
  const { projectId, dedicationId } = useParams();
  const page = useDedication(session, projectId, dedicationId);
  if (projectId === undefined || dedicationId === undefined) {
    return null;
  }
  return (
    <Shell>
      <BackLink to={`/projects/${projectId}`} label={page.projectName ?? "לפרויקט"} />
      {page.error ? <p className="error">{page.error}</p> : null}
      {page.missing ? <MissingDedication projectId={projectId} /> : null}
      {page.dedication ? (
        <DedicationBody session={session} projectId={projectId} dedication={page.dedication} onChanged={page.reload} />
      ) : null}
    </Shell>
  );
}

function MissingDedication({ projectId }: { projectId: string }) {
  return (
    <p className="empty">
      ההקדשה לא נמצאה. <Link to={`/projects/${projectId}`}>חזרה לפרויקט</Link>
    </p>
  );
}

function DedicationBody({
  session,
  projectId,
  dedication,
  onChanged,
}: {
  session: Session;
  projectId: string;
  dedication: Dedication;
  onChanged: () => void;
}) {
  const canSetPrice = session.role !== "sub_projector";
  return (
    <>
      <h1>{dedication.name}</h1>
      <DedicationActions session={session} dedication={dedication} canSetPrice={canSetPrice} onChanged={onChanged} />
      <DedicationPlacement session={session} projectId={projectId} dedication={dedication} canEdit={canSetPrice} onChanged={onChanged} />
      <ContractorCard session={session} dedication={dedication} canEdit={canSetPrice} />
      <CalculatorPanel session={session} projectId={projectId} dedication={dedication} canEditSettings={false} />
      <DonorLeads
        session={session}
        projectId={projectId}
        dedications={[dedication]}
        dedicationId={dedication.id}
        canAssign={canSetPrice}
      />
    </>
  );
}

function useDedication(session: Session, projectId: string | undefined, dedicationId: string | undefined) {
  const [projectName, setProjectName] = useState<string | null>(null);
  const [dedication, setDedication] = useState<Dedication | null>(null);
  const [missing, setMissing] = useState(false);
  const [error, setError] = useState("");
  function reload() {
    if (projectId !== undefined && dedicationId !== undefined) {
      void load(session, projectId, dedicationId, setProjectName, setDedication, setMissing, setError);
    }
  }
  useEffect(() => {
    setDedication(null);
    setMissing(false);
    reload();
  }, [session, projectId, dedicationId]);
  return { projectName, dedication, missing, error, reload };
}

async function load(
  session: Session,
  projectId: string,
  dedicationId: string,
  setProjectName: (name: string | null) => void,
  setDedication: (dedication: Dedication | null) => void,
  setMissing: (missing: boolean) => void,
  setError: (message: string) => void,
): Promise<void> {
  try {
    const projects = await listProjects(session);
    const project = projects.find((item) => item.id === projectId) ?? null;
    const dedications = project ? await listDedications(session, project.id) : [];
    setProjectName(project?.name ?? null);
    setDedication(dedications.find((item) => item.id === dedicationId) ?? null);
    setMissing(project === null || !dedications.some((item) => item.id === dedicationId));
    setError("");
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
