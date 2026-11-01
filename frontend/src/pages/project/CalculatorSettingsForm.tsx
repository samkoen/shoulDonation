import { FormEvent, useState } from "react";
import { saveCalculatorSettings, type CalculatorSettings } from "../../api";
import type { Session } from "../../session";

export function CalculatorSettingsForm({
  session,
  projectId,
  settings,
  onSaved,
}: {
  session: Session;
  projectId: string;
  settings: CalculatorSettings;
  onSaved: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(settings);
  const [error, setError] = useState("");

  if (!open) {
    return <button type="button" onClick={() => { setDraft(settings); setOpen(true); }}>כללי המחשבון</button>;
  }

  return (
    <form className="panel" onSubmit={(event) => void submit(event, session, projectId, draft, setError, setOpen, onSaved)}>
      <div className="form-grid">
        <Field label="החזר חודשי מינימלי" value={draft.minMonthly} onChange={(value) => setDraft({ ...draft, minMonthly: value })} />
        <Field label="החזר חודשי מקסימלי" value={draft.maxMonthly} onChange={(value) => setDraft({ ...draft, maxMonthly: value })} />
        <Field label="מקסימום חודשים" value={String(draft.maxMonths)} onChange={(value) => setDraft({ ...draft, maxMonths: Number(value) })} />
        <Field label="מינימום לתורם" value={draft.minPerDonor} onChange={(value) => setDraft({ ...draft, minPerDonor: value })} />
        <Field label="מקסימום לתורם" value={draft.maxPerDonor} onChange={(value) => setDraft({ ...draft, maxPerDonor: value })} />
        <Field label="מינימום תורמים" value={String(draft.minDonors)} onChange={(value) => setDraft({ ...draft, minDonors: Number(value) })} />
      </div>
      {error ? <p className="error">{error}</p> : null}
      <button type="submit">שמירת כללים</button>
    </form>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label>
      {label}
      <input value={value} onChange={(event) => onChange(event.target.value)} required />
    </label>
  );
}

async function submit(
  event: FormEvent,
  session: Session,
  projectId: string,
  draft: CalculatorSettings,
  setError: (message: string) => void,
  setOpen: (open: boolean) => void,
  onSaved: () => void,
): Promise<void> {
  event.preventDefault();
  try {
    await saveCalculatorSettings(session, projectId, draft);
    setError("");
    setOpen(false);
    onSaved();
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
