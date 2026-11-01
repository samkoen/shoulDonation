import { useState } from "react";
import type { Dedication, PlanPoint } from "../../api";
import { statusLabels } from "../../ui/labels";
import { PlanRegions } from "./PlanRegions";
import { PlanViewport } from "./PlanViewport";

export function PlanCanvas({
  url,
  dedications,
  activeId,
  placing,
  onPaint,
  onMarkerClick,
}: {
  url: string;
  dedications: Dedication[];
  activeId?: string;
  placing?: boolean;
  onPaint?: (points: PlanPoint[], width: number) => void;
  onMarkerClick?: (dedication: Dedication) => void;
}) {
  const [draft, setDraft] = useState<PlanPoint[] | null>(null);
  const placed = dedications.filter((item) => item.marker !== null);
  return (
    <PlanViewport placing={placing} onPaint={onPaint} onDraft={setDraft}>
      <div className={placing ? "plan-canvas placing" : "plan-canvas"}>
        <img src={url} alt="תוכנית האב" draggable={false} />
        <PlanRegions
          dedications={dedications}
          activeId={activeId}
          placing={placing}
          draft={draft}
          onSelect={onMarkerClick}
        />
        {placed.map((dedication) => (
          <Marker
            key={dedication.id}
            dedication={dedication}
            dimmed={activeId !== undefined && activeId !== dedication.id}
            active={activeId === dedication.id}
            onClick={placing ? undefined : onMarkerClick}
          />
        ))}
      </div>
    </PlanViewport>
  );
}

function Marker({
  dedication,
  dimmed,
  active,
  onClick,
}: {
  dedication: Dedication;
  dimmed: boolean;
  active: boolean;
  onClick?: (dedication: Dedication) => void;
}) {
  const marker = dedication.marker;
  if (marker === null) {
    return null;
  }
  const classes = ["marker", `status-${dedication.status}`, dimmed ? "dimmed" : "", active ? "active" : ""];
  return (
    <button
      type="button"
      className={classes.join(" ").trim()}
      style={{ left: `${marker.x}%`, top: `${marker.y}%` }}
      aria-label={`${dedication.name} · ${statusLabels[dedication.status]}`}
      onClick={(event) => {
        event.stopPropagation();
        onClick?.(dedication);
      }}
    >
      <span className="marker-tip">
        <strong>{dedication.name}</strong>
        <span>{dedication.price} · {statusLabels[dedication.status]}</span>
      </span>
    </button>
  );
}
