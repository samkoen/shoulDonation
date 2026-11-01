import { FormEvent, useEffect, useState } from "react";
import { getContractor, saveContractor, type Contractor, type Dedication } from "../../api";
import type { Session } from "../../session";

export function ContractorCard({
  session,
  dedication,
  canEdit,
}: {
  session: Session;
  dedication: Dedication;
  canEdit: boolean;
}) {
  if (dedication.status !== "realized") {
    return (
      <section className="workspace">
        <h2 className="section-title">קבלן</h2>
        <p className="muted">כשההקדשה מסומנת «תוקצב ומומש» אפשר לשייך כאן קבלן: שם, טלפון וסכום.</p>
      </section>
    );
  }
  return <ContractorEditor session={session} dedicationId={dedication.id} canEdit={canEdit} />;
}

function ContractorEditor({
  session,
  dedicationId,
  canEdit,
}: {
  session: Session;
  dedicationId: string;
  canEdit: boolean;
}) {
  const [contractor, setContractor] = useState<Contractor | null>(null);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getContractor(session, dedicationId)
      .then(setContractor)
      .catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "הפעולה נכשלה"));
  }, [session, dedicationId]);

  return (
    <section className="workspace">
      <h2 className="section-title">קבלן</h2>
      {error ? <p className="error">{error}</p> : null}
      {contractor ? <ContractorSummary contractor={contractor} /> : <p className="empty">אין עדיין קבלן משויך</p>}
      {canEdit && !open ? (
        <button type="button" onClick={() => setOpen(true)}>{contractor ? "עדכון קבלן" : "שיוך קבלן"}</button>
      ) : null}
      {canEdit && open ? (
        <ContractorForm
          session={session}
          dedicationId={dedicationId}
          contractor={contractor}
          onSaved={(saved) => { setContractor(saved); setOpen(false); }}
          onCancel={() => setOpen(false)}
        />
      ) : null}
    </section>
  );
}

function ContractorSummary({ contractor }: { contractor: Contractor }) {
  return (
    <article className="contractor">
      <p className="eyebrow">משויך לביצוע</p>
      <h3>{contractor.name}</h3>
      <p dir="ltr">{contractor.phone}</p>
      <p className="amount">{contractor.amount}</p>
    </article>
  );
}

function ContractorForm({
  session,
  dedicationId,
  contractor,
  onSaved,
  onCancel,
}: {
  session: Session;
  dedicationId: string;
  contractor: Contractor | null;
  onSaved: (contractor: Contractor) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(contractor?.name ?? "");
  const [phone, setPhone] = useState(contractor?.phone ?? "");
  const [amount, setAmount] = useState(contractor?.amount ?? "");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      onSaved(await saveContractor(session, dedicationId, { name, phone, amount }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  return (
    <form className="panel" onSubmit={submit}>
      <div className="form-grid">
        <label>שם הקבלן<input value={name} onChange={(event) => setName(event.target.value)} required /></label>
        <label>טלפון<input value={phone} dir="ltr" inputMode="tel" onChange={(event) => setPhone(event.target.value)} required /></label>
        <label>סכום<input value={amount} inputMode="decimal" onChange={(event) => setAmount(event.target.value)} required /></label>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="submit">שמירה</button>
        <button type="button" className="ghost" onClick={onCancel}>ביטול</button>
      </div>
    </form>
  );
}
