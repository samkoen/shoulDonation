import { useState } from "react";
import { Link } from "react-router-dom";
import { paintRegion, removeMarker, type Dedication, type PlanPoint } from "../../api";
import type { Session } from "../../session";
import { PlanCanvas } from "./PlanCanvas";
import { usePlanUrl } from "./usePlanUrl";

export function DedicationPlacement({
  session,
  projectId,
  dedication,
  canEdit,
  onChanged,
}: {
  session: Session;
  projectId: string;
  dedication: Dedication;
  canEdit: boolean;
  onChanged: () => void;
}) {
  const plan = usePlanUrl(session, projectId, 0);
  const [error, setError] = useState("");
  if (!plan.loaded || plan.url === null) {
    return null;
  }

  async function paint(points: PlanPoint[], width: number) {
    try {
      const strokes = [...(dedication.region?.kind === "brush" ? dedication.region.strokes : []), points];
      await paintRegion(session, dedication.id, { kind: "brush", width, strokes });
      setError("");
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  async function clear() {
    try {
      await removeMarker(session, dedication.id);
      setError("");
      onChanged();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  return (
    <section className="workspace">
      <h2 className="section-title">צביעה על התוכנית</h2>
      <Hint painted={dedication.region !== null} canEdit={canEdit} projectId={projectId} />
      {error ? <p className="error">{error}</p> : null}
      <PlanCanvas
        url={plan.url}
        dedications={[dedication]}
        activeId={dedication.id}
        placing={canEdit}
        onPaint={canEdit ? (points, width) => void paint(points, width) : undefined}
      />
      {canEdit && (dedication.marker || dedication.region) ? (
        <button type="button" className="ghost" onClick={() => void clear()}>מחיקת הצבע</button>
      ) : null}
    </section>
  );
}

function Hint({ painted, canEdit, projectId }: { painted: boolean; canEdit: boolean; projectId: string }) {
  if (!canEdit) {
    return <p className="muted">{painted ? "האזור צבוע על התוכנית." : "ההקדשה עדיין לא צבועה על התוכנית."}</p>;
  }
  return (
    <p className="place-callout">
      בחרו «צביעה», ואז ציירו על התוכנית עם העכבר. כל קו נוסף. «הזזה» מזיזה את המפה.{" "}
      {painted ? <Link to={`/projects/${projectId}`}>למפת החום המלאה</Link> : null}
    </p>
  );
}
