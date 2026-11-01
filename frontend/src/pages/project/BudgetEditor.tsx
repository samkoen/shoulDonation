import { FormEvent, useState } from "react";
import { saveBudget } from "../../api";
import type { Session } from "../../session";

export function BudgetEditor({
  session,
  projectId,
  onSaved,
}: {
  session: Session;
  projectId: string;
  onSaved: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [cost, setCost] = useState("");
  const [percent, setPercent] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await saveBudget(session, projectId, cost, percent);
      setError("");
      setOpen(false);
      onSaved();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  if (!open) {
    return <button type="button" onClick={() => setOpen(true)}>עדכון תקציב</button>;
  }

  return (
    <form className="panel" onSubmit={submit}>
      <label>
        עלות בנייה
        <input value={cost} onChange={(event) => setCost(event.target.value)} inputMode="decimal" required />
      </label>
      <label>
        אחוז יעד
        <input value={percent} onChange={(event) => setPercent(event.target.value)} inputMode="decimal" required />
      </label>
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="submit">שמירה</button>
        <button type="button" className="ghost" onClick={() => setOpen(false)}>ביטול</button>
      </div>
    </form>
  );
}
