import type { Dedication, PlanPaint, PlanPoint } from "../../api";
import { dedicationFill, dedicationStroke } from "../../ui/dedicationTint";

export function PlanRegions({
  dedications,
  activeId,
  placing,
  draft,
  onSelect,
}: {
  dedications: Dedication[];
  activeId?: string;
  placing?: boolean;
  draft?: PlanPoint[] | null;
  onSelect?: (dedication: Dedication) => void;
}) {
  const painted = dedications.filter((item) => item.region !== null);
  const active = dedications.find((item) => item.id === activeId);
  return (
    <svg className={placing ? "plan-regions placing" : "plan-regions"} viewBox="0 0 100 100" preserveAspectRatio="none">
      {painted.map((dedication) => (
        <PaintedRegion
          key={dedication.id}
          dedication={dedication}
          dimmed={activeId !== undefined && activeId !== dedication.id}
          active={activeId === dedication.id}
          onSelect={placing ? undefined : onSelect}
        />
      ))}
      {draft && draft.length > 0 && active ? <DraftStroke dedication={active} points={draft} /> : null}
    </svg>
  );
}

function PaintedRegion({
  dedication,
  dimmed,
  active,
  onSelect,
}: {
  dedication: Dedication;
  dimmed: boolean;
  active: boolean;
  onSelect?: (dedication: Dedication) => void;
}) {
  const region = dedication.region;
  if (region === null) {
    return null;
  }
  return (
    <g className={active ? "active" : dimmed ? "dimmed" : ""} onClick={(event) => {
      event.stopPropagation();
      onSelect?.(dedication);
    }}>
      <title>{dedication.name}</title>
      {region.kind === "polygon"
        ? <PolygonMark dedication={dedication} region={region} active={active} />
        : <BrushMarks dedication={dedication} region={region} />}
    </g>
  );
}

function PolygonMark({ dedication, region, active }: { dedication: Dedication; region: PlanPaint; active: boolean }) {
  const points = region.strokes[0] ?? [];
  return (
    <polygon
      points={points.map((point) => `${point.x},${point.y}`).join(" ")}
      fill={dedicationFill(dedication.id, dedication.status)}
      stroke={dedicationStroke(dedication.id)}
      strokeWidth={active ? 0.45 : 0.22}
    />
  );
}

function BrushMarks({ dedication, region }: { dedication: Dedication; region: PlanPaint }) {
  return (
    <>
      {region.strokes.map((stroke, index) => (
        <polyline
          key={`${dedication.id}-${index}`}
          points={stroke.map((point) => `${point.x},${point.y}`).join(" ")}
          fill="none"
          stroke={dedicationFill(dedication.id, dedication.status)}
          strokeWidth={region.width}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}
    </>
  );
}

function DraftStroke({ dedication, points }: { dedication: Dedication; points: PlanPoint[] }) {
  const width = dedication.region?.width ?? 3.5;
  return (
    <polyline
      points={points.map((point) => `${point.x},${point.y}`).join(" ")}
      fill="none"
      stroke={dedicationFill(dedication.id, dedication.status)}
      strokeWidth={width}
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  );
}
