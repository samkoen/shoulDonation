import { useEffect, useState } from "react";
import { getCalculatorSettings, listProposals, type CalculatorSettings, type Proposal } from "../../api";
import type { Dedication } from "../../api";
import type { Session } from "../../session";
import { CalculatorSettingsForm } from "./CalculatorSettingsForm";
import { ProposalList } from "./ProposalList";
import { Simulator } from "./Simulator";

export function CalculatorPanel({
  session,
  projectId,
  canEditSettings,
  dedication,
}: {
  session: Session;
  projectId: string;
  canEditSettings: boolean;
  dedication?: Dedication;
}) {
  const [settings, setSettings] = useState<CalculatorSettings | null>(null);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void load(session, projectId, setSettings, setProposals, setError);
  }, [session, projectId]);

  const reload = () => void load(session, projectId, setSettings, setProposals, setError);
  const forThisDedication = dedication
    ? proposals.filter((proposal) => proposal.dedicationId === dedication.id)
    : [];
  return (
    <section className="workspace">
      <h2 className="section-title">{dedication ? "מחשבון הצעה" : "כללי המחשבון"}</h2>
      <PanelCopy dedication={dedication} />
      {error ? <p className="error">{error}</p> : null}
      {settings ? <Bounds settings={settings} /> : null}
      {settings && canEditSettings && !dedication ? (
        <CalculatorSettingsForm session={session} projectId={projectId} settings={settings} onSaved={reload} />
      ) : null}
      {dedication ? (
        <DedicationSimulation
          session={session}
          projectId={projectId}
          dedication={dedication}
          proposals={forThisDedication}
          onChanged={reload}
        />
      ) : null}
    </section>
  );
}

function PanelCopy({ dedication }: { dedication?: Dedication }) {
  if (dedication) {
    return <p className="muted">סימולציה של החזר חודשי ומשך. «בדיקה» בודקת את הטווח, «הפקת הצעה» שומרת אותה. אין כאן חיוב.</p>;
  }
  return <p className="muted">הכללים חלים על כל ההקדשות. הסימולציה נפתחת מתוך עמוד ההקדשה.</p>;
}

function DedicationSimulation({
  session,
  projectId,
  dedication,
  proposals,
  onChanged,
}: {
  session: Session;
  projectId: string;
  dedication: Dedication;
  proposals: Proposal[];
  onChanged: () => void;
}) {
  return (
    <>
      <Simulator session={session} projectId={projectId} dedications={[dedication]} onProposed={onChanged} />
      <ProposalList session={session} proposals={proposals} dedications={[dedication]} onChanged={onChanged} />
    </>
  );
}

function Bounds({ settings }: { settings: CalculatorSettings }) {
  return (
    <p className="muted">
      {settings.minMonthly}–{settings.maxMonthly} {settings.currency} לחודש · עד {settings.maxMonths} חודשים ·{" "}
      {settings.minPerDonor}–{settings.maxPerDonor} לתורם · לפחות {settings.minDonors} תורמים
    </p>
  );
}

async function load(
  session: Session,
  projectId: string,
  setSettings: (settings: CalculatorSettings) => void,
  setProposals: (proposals: Proposal[]) => void,
  setError: (message: string) => void,
): Promise<void> {
  try {
    setSettings(await getCalculatorSettings(session, projectId));
    setProposals(await listProposals(session, projectId));
    setError("");
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
