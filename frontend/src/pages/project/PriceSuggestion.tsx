import { useState } from "react";
import { applyPricing, previewPricing, type Dedication, type PriceWeight, type PricingPreview } from "../../api";
import type { Session } from "../../session";

type Row = { dedication: Dedication; included: boolean; weight: string };

export function PriceSuggestion({
  session,
  projectId,
  dedications,
  hasBudget,
  onApplied,
}: {
  session: Session;
  projectId: string;
  dedications: Dedication[];
  hasBudget: boolean;
  onApplied: () => void;
}) {
  const [open, setOpen] = useState(false);
  if (!open) {
    return (
      <button type="button" className="ghost" disabled={!hasBudget || dedications.length === 0} onClick={() => setOpen(true)}>
        הצעת מחירים לפי היעד
      </button>
    );
  }
  return (
    <PricingPanel
      session={session}
      projectId={projectId}
      dedications={dedications}
      onClose={() => setOpen(false)}
      onApplied={() => { setOpen(false); onApplied(); }}
    />
  );
}

function PricingPanel({
  session,
  projectId,
  dedications,
  onClose,
  onApplied,
}: {
  session: Session;
  projectId: string;
  dedications: Dedication[];
  onClose: () => void;
  onApplied: () => void;
}) {
  const [rows, setRows] = useState<Row[]>(() => dedications.map((dedication) => ({ dedication, included: true, weight: "1" })));
  const [preview, setPreview] = useState<PricingPreview | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState("");
  const edit = (next: Row[]) => { setRows(next); setPreview(null); setConfirming(false); };

  async function run(action: "preview" | "apply") {
    try {
      if (action === "preview") {
        setPreview(await previewPricing(session, projectId, weightsOf(rows)));
      } else {
        await applyPricing(session, projectId, weightsOf(rows));
        onApplied();
      }
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  return (
    <div className="panel pricing">
      <h3 className="section-title">הצעת מחירים</h3>
      <p className="muted">
        המערכת מחלקת את יעד הגיוס בין ההקדשות המסומנות לפי משקל. הקדשה לא מסומנת שומרת את מחירה, והסכום שלה יורד מהיעד.
        שום מחיר לא משתנה עד שלוחצים «החלת המחירים».
      </p>
      <PricingRows rows={rows} preview={preview} onChange={edit} />
      {preview ? <Totals preview={preview} /> : null}
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="button" onClick={() => void run("preview")}>חישוב</button>
        <ApplyButton ready={preview !== null} confirming={confirming} onFirst={() => setConfirming(true)} onApply={() => void run("apply")} />
        <button type="button" className="ghost" onClick={onClose}>סגירה</button>
      </div>
    </div>
  );
}

function PricingRows({ rows, preview, onChange }: { rows: Row[]; preview: PricingPreview | null; onChange: (rows: Row[]) => void }) {
  const update = (index: number, change: Partial<Row>) => onChange(rows.map((row, i) => (i === index ? { ...row, ...change } : row)));
  return (
    <div className="pricing-rows">
      <div className="pricing-head"><span /><span>הקדשה</span><span>משקל</span><span>מחיר נוכחי</span><span>מוצע</span></div>
      {rows.map((row, index) => (
        <div key={row.dedication.id} className={row.included ? "pricing-row" : "pricing-row excluded"}>
          <input type="checkbox" checked={row.included} aria-label={`לכלול ${row.dedication.name}`} onChange={(event) => update(index, { included: event.target.checked })} />
          <span className="pricing-name">{row.dedication.name}</span>
          <input value={row.weight} inputMode="decimal" disabled={!row.included} aria-label={`משקל ${row.dedication.name}`} onChange={(event) => update(index, { weight: event.target.value })} />
          <span className="muted">{row.dedication.price}</span>
          <strong>{suggestedFor(preview, row.dedication.id) ?? "—"}</strong>
        </div>
      ))}
    </div>
  );
}

function Totals({ preview }: { preview: PricingPreview }) {
  return (
    <p className="muted">
      יעד {preview.targetAmount} · לחלוקה {preview.amountToSplit} · סה"כ מוצע{" "}
      {preview.items.reduce((sum, item) => sum + Number(item.suggestedPrice), 0).toFixed(2)}
    </p>
  );
}

function ApplyButton({ ready, confirming, onFirst, onApply }: { ready: boolean; confirming: boolean; onFirst: () => void; onApply: () => void }) {
  if (confirming) {
    return <button type="button" className="danger" onClick={onApply}>לאשר החלת המחירים</button>;
  }
  return <button type="button" disabled={!ready} onClick={onFirst}>החלת המחירים</button>;
}

function weightsOf(rows: Row[]): PriceWeight[] {
  return rows.filter((row) => row.included).map((row) => ({ dedicationId: row.dedication.id, weight: row.weight }));
}

function suggestedFor(preview: PricingPreview | null, dedicationId: string): string | null {
  return preview?.items.find((item) => item.dedicationId === dedicationId)?.suggestedPrice ?? null;
}
