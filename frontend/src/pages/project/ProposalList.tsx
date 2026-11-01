import { FormEvent, useState } from "react";
import { deleteProposal, updateProposal, type Dedication, type Proposal } from "../../api";
import type { Session } from "../../session";

export function ProposalList({
  session,
  proposals,
  dedications,
  onChanged,
}: {
  session: Session;
  proposals: Proposal[];
  dedications: Dedication[];
  onChanged: () => void;
}) {
  if (proposals.length === 0) {
    return <p className="empty">אין עדיין הצעה</p>;
  }
  return (
    <div className="grid">
      {proposals.map((proposal) => (
        <ProposalCard
          key={proposal.id}
          session={session}
          proposal={proposal}
          dedications={dedications}
          onChanged={onChanged}
        />
      ))}
    </div>
  );
}

function ProposalCard({
  session,
  proposal,
  dedications,
  onChanged,
}: {
  session: Session;
  proposal: Proposal;
  dedications: Dedication[];
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState("");
  if (editing) {
    return (
      <ProposalEditor
        session={session}
        proposal={proposal}
        dedications={dedications}
        onClose={() => setEditing(false)}
        onChanged={onChanged}
      />
    );
  }
  return (
    <article className="proposal">
      <p className="eyebrow">ממתין לטבלת ריבית</p>
      {dedications.length > 1 ? <h2>{nameOf(dedications, proposal.dedicationId)}</h2> : null}
      <p className="amount">{proposal.monthlyAmount} <small>{proposal.currency} / חודש</small></p>
      <p className="muted">{proposal.months} חודשים · {proposal.donorCount} תורמים</p>
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="button" className="ghost" onClick={() => setEditing(true)}>עריכה</button>
        {confirming ? (
          <button type="button" className="danger" onClick={() => void remove(session, proposal.id, setError, onChanged)}>לאשר מחיקה</button>
        ) : (
          <button type="button" className="danger" onClick={() => setConfirming(true)}>מחיקה</button>
        )}
      </div>
    </article>
  );
}

function ProposalEditor({
  session,
  proposal,
  dedications,
  onClose,
  onChanged,
}: {
  session: Session;
  proposal: Proposal;
  dedications: Dedication[];
  onClose: () => void;
  onChanged: () => void;
}) {
  const [dedicationId, setDedicationId] = useState(proposal.dedicationId);
  const [monthly, setMonthly] = useState(proposal.monthlyAmount);
  const [months, setMonths] = useState(String(proposal.months));
  const [donors, setDonors] = useState(String(proposal.donorCount));
  const [error, setError] = useState("");
  return (
    <form className="proposal" onSubmit={(event) => void save(event, session, proposal.id, dedicationId, monthly, months, donors, setError, onClose, onChanged)}>
      {dedications.length > 1 ? (
        <label>
          הקדשה
          <select value={dedicationId} onChange={(event) => setDedicationId(event.target.value)}>
            {dedications.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
      ) : null}
      <label>החזר חודשי<input value={monthly} onChange={(event) => setMonthly(event.target.value)} required /></label>
      <label>חודשים<input value={months} onChange={(event) => setMonths(event.target.value)} required /></label>
      <label>מספר תורמים<input value={donors} onChange={(event) => setDonors(event.target.value)} required /></label>
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="submit">שמירה</button>
        <button type="button" className="ghost" onClick={onClose}>ביטול</button>
      </div>
    </form>
  );
}

function nameOf(dedications: Dedication[], dedicationId: string): string {
  return dedications.find((item) => item.id === dedicationId)?.name ?? "הקדשה";
}

async function remove(
  session: Session,
  proposalId: string,
  setError: (message: string) => void,
  onChanged: () => void,
): Promise<void> {
  try {
    await deleteProposal(session, proposalId);
    setError("");
    onChanged();
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}

async function save(
  event: FormEvent,
  session: Session,
  proposalId: string,
  dedicationId: string,
  monthly: string,
  months: string,
  donors: string,
  setError: (message: string) => void,
  onClose: () => void,
  onChanged: () => void,
): Promise<void> {
  event.preventDefault();
  try {
    await updateProposal(session, proposalId, {
      dedicationId,
      monthlyAmount: monthly,
      months: Number(months),
      donorCount: Number(donors),
    });
    setError("");
    onClose();
    onChanged();
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
