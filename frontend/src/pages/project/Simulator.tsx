import { FormEvent, useState } from "react";
import {
  createProposal,
  previewSimulation,
  type Dedication,
  type Simulation,
  type SimulationDraft,
} from "../../api";
import type { Session } from "../../session";

export function Simulator({
  session,
  projectId,
  dedications,
  onProposed,
}: {
  session: Session;
  projectId: string;
  dedications: Dedication[];
  onProposed: () => void;
}) {
  const form = useDraft(dedications);
  if (dedications.length === 0) {
    return <p className="empty">אין עדיין הקדשה למחשבון</p>;
  }
  return (
    <form className="panel" onSubmit={(event) => void check(event, session, projectId, form)}>
      <DraftFields dedications={dedications} form={form} />
      <div className="row">
        <button type="submit">בדיקה</button>
        <button type="button" disabled={!accepted(form.preview) || form.saving} onClick={() => void issue(session, projectId, form, onProposed)}>
          הפקת הצעה
        </button>
      </div>
      {form.error ? <p className="error">{form.error}</p> : null}
      {form.preview ? <CheckList preview={form.preview} /> : null}
    </form>
  );
}

function DraftFields({ dedications, form }: { dedications: Dedication[]; form: DraftForm }) {
  return (
    <div className="form-grid">
      {dedications.length > 1 ? (
        <label>
          הקדשה
          <select value={form.dedicationId} onChange={(event) => form.editDedication(event.target.value)}>
            {dedications.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
      ) : null}
      <label>
        החזר חודשי
        <input value={form.monthly} onChange={(event) => form.editMonthly(event.target.value)} inputMode="decimal" required />
      </label>
      <label>
        חודשים
        <input value={form.months} onChange={(event) => form.editMonths(event.target.value)} inputMode="numeric" required />
      </label>
      <label>
        מספר תורמים
        <input value={form.donors} onChange={(event) => form.editDonors(event.target.value)} inputMode="numeric" required />
      </label>
    </div>
  );
}

function CheckList({ preview }: { preview: Simulation }) {
  return (
    <div className="check-list">
      <span className={pill(preview.monthlyWithinRange)}>{preview.monthlyWithinRange ? "החזר בטווח" : "החזר מחוץ לטווח"}</span>
      <span className={pill(preview.termWithinLimit)}>{preview.termWithinLimit ? "משך בטווח" : "משך מחוץ לטווח"}</span>
      <span className={pill(preview.donorsMeetMinimum)}>{preview.donorsMeetMinimum ? "מספיק תורמים" : "חסרים תורמים"}</span>
      <span className="check-wait">הסכום הממומן ממתין לטבלת הריביות</span>
    </div>
  );
}

function useDraft(dedications: Dedication[]): DraftForm {
  const [dedicationId, setDedicationId] = useState(dedications[0]?.id ?? "");
  const [monthly, setMonthly] = useState("120.00");
  const [months, setMonths] = useState("36");
  const [donors, setDonors] = useState("10");
  const [preview, setPreview] = useState<Simulation | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const clear = () => setPreview(null);
  return {
    dedicationId: dedicationId || dedications[0]?.id || "",
    monthly,
    months,
    donors,
    preview,
    error,
    saving,
    setPreview,
    setError,
    setSaving,
    editDedication: (value) => { setDedicationId(value); clear(); },
    editMonthly: (value) => { setMonthly(value); clear(); },
    editMonths: (value) => { setMonths(value); clear(); },
    editDonors: (value) => { setDonors(value); clear(); },
  };
}

type DraftForm = {
  dedicationId: string;
  monthly: string;
  months: string;
  donors: string;
  preview: Simulation | null;
  error: string;
  saving: boolean;
  setPreview: (preview: Simulation | null) => void;
  setError: (message: string) => void;
  setSaving: (saving: boolean) => void;
  editDedication: (value: string) => void;
  editMonthly: (value: string) => void;
  editMonths: (value: string) => void;
  editDonors: (value: string) => void;
};

function pill(ok: boolean): string {
  return ok ? "check-ok" : "check-bad";
}

function accepted(preview: Simulation | null): boolean {
  return preview !== null && preview.monthlyWithinRange && preview.termWithinLimit && preview.donorsMeetMinimum;
}

function draftOf(form: DraftForm): SimulationDraft {
  return {
    dedicationId: form.dedicationId,
    monthlyAmount: form.monthly,
    months: Number(form.months),
    donorCount: Number(form.donors),
  };
}

async function check(event: FormEvent, session: Session, projectId: string, form: DraftForm): Promise<void> {
  event.preventDefault();
  try {
    form.setPreview(await previewSimulation(session, projectId, draftOf(form)));
    form.setError("");
  } catch (caught) {
    form.setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}

async function issue(session: Session, projectId: string, form: DraftForm, onProposed: () => void): Promise<void> {
  form.setSaving(true);
  try {
    await createProposal(session, projectId, draftOf(form));
    form.setPreview(null);
    form.setError("");
    onProposed();
  } catch (caught) {
    form.setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  } finally {
    form.setSaving(false);
  }
}
