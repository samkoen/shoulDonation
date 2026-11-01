import { FormEvent, useEffect, useState } from "react";
import {
  createMeeting,
  listMeetings,
  updateLead,
  type Assignee,
  type Dedication,
  type Lead,
  type LeadStatus,
  type Meeting,
} from "../../api";
import type { Session } from "../../session";
import { leadStatusLabels } from "../../ui/labels";

export function LeadCard({
  session,
  lead,
  dedications,
  assignees,
  showDedication = true,
  onChanged,
}: {
  session: Session;
  lead: Lead;
  dedications: Dedication[];
  assignees: Assignee[];
  showDedication?: boolean;
  onChanged: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const dedication = dedications.find((item) => item.id === lead.dedicationId)?.name;
  const assignee = assignees.find((item) => item.userId === lead.assigneeId)?.email;

  async function changeStatus(status: LeadStatus) {
    setSaving(true);
    try {
      await updateLead(session, lead.id, status);
      setError("");
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    } finally {
      setSaving(false);
    }
  }

  return (
    <article className={`lead status-${lead.status}`}>
      <p className="eyebrow">{leadStatusLabels[lead.status]}</p>
      <h2>{lead.name}</h2>
      <p>{lead.phone}</p>
      {showDedication && dedication ? <p className="muted">{dedication}</p> : null}
      {assignee ? <p className="muted">{assignee}</p> : null}
      <StatusSwitch value={lead.status} disabled={saving} onChange={(status) => void changeStatus(status)} />
      {error ? <p className="error">{error}</p> : null}
      <Meetings session={session} leadId={lead.id} />
    </article>
  );
}

function StatusSwitch({
  value,
  disabled,
  onChange,
}: {
  value: LeadStatus;
  disabled: boolean;
  onChange: (status: LeadStatus) => void;
}) {
  return (
    <div className="segments">
      {(Object.keys(leadStatusLabels) as LeadStatus[]).map((status) => (
        <button key={status} type="button" className={status === value ? `active lead-${status}` : `lead-${status}`} disabled={disabled} onClick={() => onChange(status)}>
          {leadStatusLabels[status]}
        </button>
      ))}
    </div>
  );
}

function Meetings({ session, leadId }: { session: Session; leadId: string }) {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [when, setWhen] = useState("");
  const [note, setNote] = useState("");
  const [chance, setChance] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    void load(session, leadId, setMeetings, setError);
  }, [session, leadId]);

  return (
    <div className="meetings">
      {meetings.map((meeting) => (
        <p key={meeting.id} className="muted">
          {formatWhen(meeting.scheduledAt)}
          {meeting.closeChance ? ` · סיכוי ${meeting.closeChance}%` : ""}
          {meeting.note ? ` · ${meeting.note}` : ""}
        </p>
      ))}
      <form onSubmit={(event) => void add(event, session, leadId, when, note, chance, setWhen, setNote, setChance, setMeetings, setError)}>
        <label>
          פגישה
          <input type="datetime-local" value={when} onChange={(event) => setWhen(event.target.value)} required />
        </label>
        <label>
          הערה
          <input value={note} onChange={(event) => setNote(event.target.value)} />
        </label>
        <ChanceField value={chance} onChange={setChance} />
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">קביעת פגישה</button>
      </form>
    </div>
  );
}

function ChanceField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <div>
      <p className="muted">סיכוי סגירה לפי הערכת הפגישה. אין כאן חישוב אוטומטי.</p>
      <div className="chips">
        {["30", "50", "70", "90"].map((item) => (
          <button key={item} type="button" className={value === item ? "chip active" : "chip"} onClick={() => onChange(item)}>
            {item}%
          </button>
        ))}
      </div>
      <label>
        אחוז
        <input value={value} inputMode="numeric" placeholder="אופציונלי" onChange={(event) => onChange(event.target.value)} />
      </label>
    </div>
  );
}

function formatWhen(value: string): string {
  return new Date(value).toLocaleString("he-IL", { dateStyle: "short", timeStyle: "short" });
}

async function load(
  session: Session,
  leadId: string,
  setMeetings: (meetings: Meeting[]) => void,
  setError: (message: string) => void,
): Promise<void> {
  try {
    setMeetings(await listMeetings(session, leadId));
    setError("");
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}

async function add(
  event: FormEvent,
  session: Session,
  leadId: string,
  when: string,
  note: string,
  chance: string,
  setWhen: (value: string) => void,
  setNote: (value: string) => void,
  setChance: (value: string) => void,
  setMeetings: (meetings: Meeting[]) => void,
  setError: (message: string) => void,
): Promise<void> {
  event.preventDefault();
  try {
    await createMeeting(session, leadId, when, note, chance);
    setWhen("");
    setNote("");
    setChance("");
    await load(session, leadId, setMeetings, setError);
  } catch (caught) {
    setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
