import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { createDedication, updateDedication, type Dedication } from "../../api";
import type { Session } from "../../session";
import { ColorSwatch } from "../../ui/ColorSwatch";
import { statusLabels } from "../../ui/labels";

export function DedicationCreator({
  session,
  projectId,
  onCreated,
}: {
  session: Session;
  projectId: string;
  onCreated: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await createDedication(session, projectId, name, price);
      setName("");
      setPrice("");
      setError("");
      setOpen(false);
      onCreated();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  if (!open) {
    return <button type="button" onClick={() => setOpen(true)}>הקדשה חדשה</button>;
  }

  return (
    <form className="panel" onSubmit={submit}>
      <label>
        שם ההקדשה
        <input value={name} onChange={(event) => setName(event.target.value)} required />
      </label>
      <label>
        מחיר
        <input value={price} onChange={(event) => setPrice(event.target.value)} inputMode="decimal" required />
      </label>
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="submit">הוספה</button>
        <button type="button" className="ghost" onClick={() => setOpen(false)}>ביטול</button>
      </div>
    </form>
  );
}

export function DedicationCatalog({ projectId, dedications }: { projectId: string; dedications: Dedication[] }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<Dedication["status"] | "all">("all");
  if (dedications.length === 0) {
    return <p className="empty">אין עדיין הקדשות</p>;
  }
  const visible = dedications.filter((item) => matches(item, query, status));
  return (
    <div className="workspace">
      <CatalogFilters query={query} status={status} onQuery={setQuery} onStatus={setStatus} />
      <p className="muted">{visible.length} מתוך {dedications.length}</p>
      <div className="catalog">
        {visible.map((dedication) => (
          <CatalogRow key={dedication.id} projectId={projectId} dedication={dedication} />
        ))}
      </div>
      {visible.length === 0 ? <p className="empty">אין הקדשה שמתאימה לחיפוש</p> : null}
    </div>
  );
}

function CatalogFilters({
  query,
  status,
  onQuery,
  onStatus,
}: {
  query: string;
  status: Dedication["status"] | "all";
  onQuery: (value: string) => void;
  onStatus: (value: Dedication["status"] | "all") => void;
}) {
  return (
    <div className="catalog-tools">
      <input value={query} placeholder="חיפוש הקדשה" onChange={(event) => onQuery(event.target.value)} />
      <div className="chips">
        <button type="button" className={status === "all" ? "chip active" : "chip"} onClick={() => onStatus("all")}>הכל</button>
        {(Object.keys(statusLabels) as Dedication["status"][]).map((item) => (
          <button key={item} type="button" className={status === item ? `chip active status-${item}` : "chip"} onClick={() => onStatus(item)}>
            {statusLabels[item]}
          </button>
        ))}
      </div>
    </div>
  );
}

function CatalogRow({ projectId, dedication }: { projectId: string; dedication: Dedication }) {
  return (
    <Link className={`catalog-row status-${dedication.status}`} to={`/projects/${projectId}/dedications/${dedication.id}`}>
      <ColorSwatch dedicationId={dedication.id} />
      <span className="eyebrow">{statusLabels[dedication.status]}{dedication.region || dedication.marker ? " · על התוכנית" : ""}</span>
      <span className="catalog-name">{dedication.name}</span>
      <strong className="catalog-price">{dedication.price}</strong>
    </Link>
  );
}

function matches(dedication: Dedication, query: string, status: Dedication["status"] | "all"): boolean {
  const haystack = dedication.name.includes(query.trim());
  return haystack && (status === "all" || dedication.status === status);
}

export function DedicationActions({
  session,
  dedication,
  canSetPrice,
  onChanged,
}: {
  session: Session;
  dedication: Dedication;
  canSetPrice: boolean;
  onChanged: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function changeStatus(status: Dedication["status"]) {
    setSaving(true);
    try {
      await updateDedication(session, dedication.id, { status });
      setError("");
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    } finally {
      setSaving(false);
    }
  }

  return (
    <article className={`dedication status-${dedication.status}`}>
      <p className="eyebrow">{statusLabels[dedication.status]}</p>
      <p className="amount">{dedication.price}</p>
      <StatusSwitch value={dedication.status} disabled={saving} onChange={(status) => void changeStatus(status)} />
      {error ? <p className="error">{error}</p> : null}
      {canSetPrice ? <PriceEditor session={session} dedication={dedication} onChanged={onChanged} /> : null}
    </article>
  );
}

function StatusSwitch({
  value,
  disabled,
  onChange,
}: {
  value: Dedication["status"];
  disabled: boolean;
  onChange: (status: Dedication["status"]) => void;
}) {
  return (
    <div className="segments">
      {(Object.keys(statusLabels) as Dedication["status"][]).map((status) => (
        <button
          key={status}
          type="button"
          className={status === value ? "active" : ""}
          disabled={disabled}
          onClick={() => onChange(status)}
        >
          {statusLabels[status]}
        </button>
      ))}
    </div>
  );
}

function PriceEditor({
  session,
  dedication,
  onChanged,
}: {
  session: Session;
  dedication: Dedication;
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [price, setPrice] = useState(dedication.price);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await updateDedication(session, dedication.id, { price });
      setError("");
      setOpen(false);
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  if (!open) {
    return <button type="button" className="ghost" onClick={() => setOpen(true)}>עדכון מחיר</button>;
  }

  return (
    <form onSubmit={submit}>
      <input value={price} onChange={(event) => setPrice(event.target.value)} inputMode="decimal" required />
      {error ? <p className="error">{error}</p> : null}
      <button type="submit">שמירה</button>
    </form>
  );
}
