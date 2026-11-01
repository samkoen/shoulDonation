import { FormEvent, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { createCustomerLead, listCustomerLeads, type Lead } from "../api";
import { BackLink } from "../components/BackLink";
import { Shell } from "../components/Shell";
import { useRequiredSession } from "../session/SessionProvider";
import type { Session } from "../session";
import { leadStatusLabels } from "../ui/labels";

export function CustomerLeadsPage() {
  const { session } = useRequiredSession();
  if (session.role !== "platform_admin") {
    return <Navigate to="/" replace />;
  }
  return <CustomerHome session={session} />;
}

function CustomerHome({ session }: { session: Session }) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    void load(session, setLeads, setError);
  }, [session]);

  return (
    <Shell>
      <BackLink to="/" label="לבתי הכנסת" />
      <h1>פניות לבית כנסת חדש</h1>
      {error ? <p className="error">{error}</p> : null}
      <CustomerForm session={session} onCreated={() => void load(session, setLeads, setError)} />
      {leads.length === 0 ? <p className="empty">אין עדיין פנייה</p> : null}
      <div className="grid">
        {leads.map((lead) => (
          <article className={`lead status-${lead.status}`} key={lead.id}>
            <p className="eyebrow">{leadStatusLabels[lead.status]}</p>
            <h2>{lead.requestedSynagogueName}</h2>
            <p>{lead.name}</p>
            <p className="muted">{lead.phone}</p>
          </article>
        ))}
      </div>
    </Shell>
  );
}

function CustomerForm({ session, onCreated }: { session: Session; onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [synagogueName, setSynagogueName] = useState("");
  const [error, setError] = useState("");
  if (!open) {
    return <button type="button" onClick={() => setOpen(true)}>פנייה חדשה</button>;
  }
  return (
    <form className="panel" onSubmit={(event) => void submit(event, session, name, phone, synagogueName, setError, setOpen, onCreated)}>
      <div className="form-grid">
        <label>שם<input value={name} onChange={(event) => setName(event.target.value)} required /></label>
        <label>טלפון<input value={phone} onChange={(event) => setPhone(event.target.value)} required /></label>
        <label>בית הכנסת<input value={synagogueName} onChange={(event) => setSynagogueName(event.target.value)} required /></label>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <button type="submit">שמירה</button>
    </form>
  );
}

async function load(session: Session, setLeads: (leads: Lead[]) => void, setError: (message: string) => void): Promise<void> {
  try {
    setLeads(await listCustomerLeads(session));
    setError("");
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}

async function submit(
  event: FormEvent,
  session: Session,
  name: string,
  phone: string,
  synagogueName: string,
  setError: (message: string) => void,
  setOpen: (open: boolean) => void,
  onCreated: () => void,
): Promise<void> {
  event.preventDefault();
  try {
    await createCustomerLead(session, name, phone, synagogueName);
    setError("");
    setOpen(false);
    onCreated();
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
