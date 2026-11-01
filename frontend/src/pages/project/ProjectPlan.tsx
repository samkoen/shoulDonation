import { ChangeEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { paintRegion, uploadPlan, type Dedication, type PlanPoint } from "../../api";
import type { Session } from "../../session";
import { ColorSwatch } from "../../ui/ColorSwatch";
import { statusLabels } from "../../ui/labels";
import { PlanCanvas } from "./PlanCanvas";
import { usePlanUrl } from "./usePlanUrl";

export function ProjectPlan({
  session,
  projectId,
  dedications,
  canReplace,
  onChanged,
}: {
  session: Session;
  projectId: string;
  dedications: Dedication[];
  canReplace: boolean;
  onChanged: () => void;
}) {
  const [version, setVersion] = useState(0);
  const [error, setError] = useState("");
  const plan = usePlanUrl(session, projectId, version);
  const navigate = useNavigate();
  const message = error || plan.error;
  return (
    <section className="workspace">
      <h2 className="section-title">תוכנית האב ומפת חום</h2>
      <Legend />
      {message ? <p className="error">{message}</p> : null}
      {plan.url ? (
        <Heatmap
          session={session}
          url={plan.url}
          dedications={dedications}
          canPlace={canReplace}
          onOpen={(dedication) => navigate(`/projects/${projectId}/dedications/${dedication.id}`)}
          onChanged={onChanged}
          onError={setError}
        />
      ) : null}
      {plan.loaded && !plan.url ? <EmptyPlan canReplace={canReplace} /> : null}
      {canReplace ? (
        <PlanFile
          session={session}
          projectId={projectId}
          hasPlan={plan.url !== null}
          onUploaded={() => setVersion((value) => value + 1)}
          onError={setError}
        />
      ) : null}
    </section>
  );
}

function Legend() {
  return (
    <div className="legend">
      {(Object.keys(statusLabels) as Dedication["status"][]).map((status) => (
        <span key={status} className={`legend-item status-${status}`}>{statusLabels[status]}</span>
      ))}
      <span className="muted">כל הקדשה בצבע משלה על התוכנית וברשימה.</span>
    </div>
  );
}

function EmptyPlan({ canReplace }: { canReplace: boolean }) {
  return (
    <p className="empty">
      {canReplace ? "אין עדיין תוכנית. העלו תמונה של תוכנית האב כדי למקם עליה את ההקדשות." : "אין עדיין תוכנית."}
    </p>
  );
}

function Heatmap({
  session,
  url,
  dedications,
  canPlace,
  onOpen,
  onChanged,
  onError,
}: {
  session: Session;
  url: string;
  dedications: Dedication[];
  canPlace: boolean;
  onOpen: (dedication: Dedication) => void;
  onChanged: () => void;
  onError: (message: string) => void;
}) {
  const [selectedId, setSelectedId] = useState("");
  const selected = dedications.find((item) => item.id === selectedId) ?? null;

  async function paint(points: PlanPoint[], width: number) {
    if (!selected) {
      return;
    }
    try {
      const strokes = [...(selected.region?.kind === "brush" ? selected.region.strokes : []), points];
      await paintRegion(session, selected.id, { kind: "brush", width, strokes });
      onError("");
      onChanged();
    } catch (caught) {
      onError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  return (
    <>
      {canPlace ? (
        <PlacementBar dedications={dedications} selectedId={selectedId} onSelect={setSelectedId} />
      ) : null}
      <PlanCanvas
        url={url}
        dedications={dedications}
        activeId={selected?.id}
        placing={selected !== null}
        onPaint={(points, width) => void paint(points, width)}
        onMarkerClick={onOpen}
      />
    </>
  );
}

function PlacementBar({
  dedications,
  selectedId,
  onSelect,
}: {
  dedications: Dedication[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const [query, setQuery] = useState("");
  const unplaced = dedications.filter((item) => item.marker === null);
  const shown = dedications.filter((item) => item.name.includes(query.trim()) || item.id === selectedId);
  return (
    <div className="placement-bar">
      <p className="place-callout">
        {selectedId
          ? "ההקדשה נבחרה. ציירו על התוכנית כדי לצבוע את האזור. «הזזה» אם צריך להזיז את המפה."
          : `בחרו הקדשה כאן, אחר כך ציירו על התוכנית. ${unplaced.length} עדיין בלי צבע.`}
      </p>
      <input value={query} placeholder="חיפוש הקדשה למיקום" onChange={(event) => setQuery(event.target.value)} />
      <div className="place-list">
        {shown.slice(0, 12).map((item) => (
          <button
            key={item.id}
            type="button"
            className={`place-chip status-${item.status}${selectedId === item.id ? " selected" : ""}`}
            onClick={() => onSelect(selectedId === item.id ? "" : item.id)}
          >
            <ColorSwatch dedicationId={item.id} />
            <span>{item.region || item.marker ? "●" : "○"}</span>
            <span>{item.name}</span>
          </button>
        ))}
      </div>
      {shown.length > 12 ? <p className="muted">עוד {shown.length - 12}. צמצמו את החיפוש.</p> : null}
    </div>
  );
}

function PlanFile({
  session,
  projectId,
  hasPlan,
  onUploaded,
  onError,
}: {
  session: Session;
  projectId: string;
  hasPlan: boolean;
  onUploaded: () => void;
  onError: (message: string) => void;
}) {
  return (
    <label className="file-button">
      {hasPlan ? "החלפת תוכנית" : "העלאת תוכנית"}
      <input
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={(event) => void send(event, session, projectId, onUploaded, onError)}
      />
    </label>
  );
}

async function send(
  event: ChangeEvent<HTMLInputElement>,
  session: Session,
  projectId: string,
  onUploaded: () => void,
  onError: (message: string) => void,
): Promise<void> {
  const file = event.target.files?.[0];
  event.target.value = "";
  if (!file) {
    return;
  }
  try {
    await uploadPlan(session, projectId, file);
    onError("");
    onUploaded();
  } catch (caught) {
    onError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
