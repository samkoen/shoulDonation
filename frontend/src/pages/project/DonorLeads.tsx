import { FormEvent, useEffect, useState } from "react";
import {
  createDonorLead,
  listAssignees,
  listDonorLeads,
  type Assignee,
  type Dedication,
  type Lead,
} from "../../api";
import type { Session } from "../../session";
import { LeadCard } from "./LeadCard";

export function DonorLeads({
  session,
  projectId,
  dedications,
  dedicationId,
  canAssign,
}: {
  session: Session;
  projectId: string;
  dedications: Dedication[];
  dedicationId: string;
  canAssign: boolean;
}) {
  const board = useLeadBoard(session, projectId);
  const visible = board.leads.filter((lead) => lead.dedicationId === dedicationId);
  return (
    <section className="workspace">
      <h2 className="section-title">לידים של תורמים</h2>
      {board.error ? <p className="error">{board.error}</p> : null}
      <DonorForm
        session={session}
        projectId={projectId}
        dedicationId={dedicationId}
        assignees={board.assignees}
        canAssign={canAssign}
        onCreated={board.reload}
      />
      {visible.length === 0 ? <p className="empty">אין עדיין ליד להקדשה הזו</p> : null}
      <LeadStack leads={visible} session={session} dedications={dedications} assignees={board.assignees} onChanged={board.reload} />
    </section>
  );
}

export function UnassignedLeads({
  session,
  projectId,
  dedications,
}: {
  session: Session;
  projectId: string;
  dedications: Dedication[];
}) {
  const board = useLeadBoard(session, projectId);
  const visible = board.leads.filter((lead) => lead.dedicationId === null);
  if (!board.error && visible.length === 0) {
    return null;
  }
  return (
    <section className="workspace">
      <h2 className="section-title">לידים בלי הקדשה</h2>
      {board.error ? <p className="error">{board.error}</p> : null}
      <LeadStack leads={visible} session={session} dedications={dedications} assignees={board.assignees} onChanged={board.reload} />
    </section>
  );
}

function LeadStack({
  leads,
  session,
  dedications,
  assignees,
  onChanged,
}: {
  leads: Lead[];
  session: Session;
  dedications: Dedication[];
  assignees: Assignee[];
  onChanged: () => void;
}) {
  return (
    <div className="stack">
      {leads.map((lead) => (
        <LeadCard
          key={lead.id}
          session={session}
          lead={lead}
          dedications={dedications}
          assignees={assignees}
          showDedication={false}
          onChanged={onChanged}
        />
      ))}
    </div>
  );
}

function useLeadBoard(session: Session, projectId: string) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [assignees, setAssignees] = useState<Assignee[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    void load(session, projectId, setLeads, setAssignees, setError);
  }, [session, projectId]);
  return { leads, assignees, error, reload: () => void load(session, projectId, setLeads, setAssignees, setError) };
}

function DonorForm({
  session,
  projectId,
  dedicationId,
  assignees,
  canAssign,
  onCreated,
}: {
  session: Session;
  projectId: string;
  dedicationId: string;
  assignees: Assignee[];
  canAssign: boolean;
  onCreated: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [assigneeId, setAssigneeId] = useState("");
  const [error, setError] = useState("");
  if (!open) {
    return <button type="button" onClick={() => setOpen(true)}>ליד חדש</button>;
  }
  return (
    <form className="panel" onSubmit={(event) => void submit(event, { session, projectId, name, phone, dedicationId, assigneeId, setError, setOpen, onCreated })}>
      <div className="form-grid">
        <Field label="שם" value={name} onChange={setName} />
        <Field label="טלפון" value={phone} onChange={setPhone} />
        {canAssign ? <AssigneeSelect assignees={assignees} value={assigneeId} onChange={setAssigneeId} /> : null}
      </div>
      {error ? <p className="error">{error}</p> : null}
      <button type="submit">שמירה</button>
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

function AssigneeSelect({ assignees, value, onChange }: { assignees: Assignee[]; value: string; onChange: (value: string) => void }) {
  return (
    <label>
      תת-פרויקטור
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">בלי שיוך</option>
        {assignees.map((item) => <option key={item.userId} value={item.userId}>{item.email}</option>)}
      </select>
    </label>
  );
}

async function load(
  session: Session,
  projectId: string,
  setLeads: (leads: Lead[]) => void,
  setAssignees: (assignees: Assignee[]) => void,
  setError: (message: string) => void,
): Promise<void> {
  try {
    setLeads(await listDonorLeads(session, projectId));
    setAssignees(await listAssignees(session, projectId));
    setError("");
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}

async function submit(
  event: FormEvent,
  input: {
    session: Session;
    projectId: string;
    name: string;
    phone: string;
    dedicationId: string;
    assigneeId: string;
    setError: (message: string) => void;
    setOpen: (open: boolean) => void;
    onCreated: () => void;
  },
): Promise<void> {
  event.preventDefault();
  try {
    await createDonorLead(input.session, input.projectId, input);
    input.setError("");
    input.setOpen(false);
    input.onCreated();
  } catch (caught) {
    input.setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
