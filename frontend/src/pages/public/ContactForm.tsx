import { FormEvent, useState } from "react";
import { submitPublicContact } from "../../api";

type Draft = { name: string; phone: string; synagogueName: string };

const EMPTY: Draft = { name: "", phone: "", synagogueName: "" };

export function ContactForm({ slug }: { slug: string }) {
  const [draft, setDraft] = useState<Draft>(EMPTY);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await submitPublicContact(slug, draft);
      setDraft(EMPTY);
      setError("");
      setSent(true);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  if (sent) {
    return (
      <div className="panel">
        <strong>תודה, הפרטים התקבלו.</strong>
        <p className="muted">נחזור אליכם בהקדם.</p>
      </div>
    );
  }

  return (
    <form className="panel" onSubmit={submit}>
      <div className="form-grid">
        <label>
          שם מלא
          <input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} required />
        </label>
        <label>
          טלפון
          <input
            value={draft.phone}
            inputMode="tel"
            dir="ltr"
            onChange={(event) => setDraft({ ...draft, phone: event.target.value })}
            required
          />
        </label>
        <label>
          בית הכנסת
          <input
            value={draft.synagogueName}
            onChange={(event) => setDraft({ ...draft, synagogueName: event.target.value })}
            required
          />
        </label>
      </div>
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="submit">שליחה</button>
      </div>
    </form>
  );
}
