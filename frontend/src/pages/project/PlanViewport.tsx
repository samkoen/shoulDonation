import { MutableRefObject, PointerEvent, ReactNode, RefObject, useEffect, useRef, useState } from "react";
import type { PlanPoint } from "../../api";

const MIN_SCALE = 1;
const MAX_SCALE = 6;
const SAMPLE_GAP = 0.45;

export function PlanViewport({
  placing,
  children,
  onPaint,
  onDraft,
}: {
  placing?: boolean;
  children: ReactNode;
  onPaint?: (points: PlanPoint[], width: number) => void;
  onDraft?: (points: PlanPoint[] | null) => void;
}) {
  const stageRef = useRef<HTMLDivElement>(null);
  const drag = useRef<DragState | null>(null);
  const [tool, setTool] = useState<"paint" | "pan">("paint");
  const [width, setWidth] = useState(3.5);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const painting = Boolean(placing && tool === "paint" && onPaint);
  useWheelZoom(stageRef, scale, offset, setScale, setOffset);
  return (
    <div className="plan-viewport">
      <ZoomBar
        scale={scale}
        painting={Boolean(placing)}
        tool={tool}
        width={width}
        onTool={setTool}
        onWidth={setWidth}
        onZoom={setScale}
        onReset={() => resetView(setScale, setOffset)}
      />
      <div
        ref={stageRef}
        className={stageClass(placing, painting)}
        onPointerDown={(event) => startPointer(event, drag, offset, painting, onDraft)}
        onPointerMove={(event) => movePointer(event, drag, painting, setOffset, onDraft)}
        onPointerUp={() => endPointer(drag, painting, width, onPaint, onDraft)}
        onPointerCancel={() => cancelPointer(drag, onDraft)}
      >
        <div className="plan-world" style={{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})` }}>
          {children}
        </div>
      </div>
    </div>
  );
}

type DragState = {
  x: number;
  y: number;
  ox: number;
  oy: number;
  moved: boolean;
  points: PlanPoint[];
};

function ZoomBar({
  scale,
  painting,
  tool,
  width,
  onTool,
  onWidth,
  onZoom,
  onReset,
}: {
  scale: number;
  painting: boolean;
  tool: "paint" | "pan";
  width: number;
  onTool: (tool: "paint" | "pan") => void;
  onWidth: (width: number) => void;
  onZoom: (scale: number) => void;
  onReset: () => void;
}) {
  return (
    <div className="plan-zoom">
      <button type="button" className="ghost" onClick={() => onZoom(clampScale(scale / 1.25))} aria-label="הקטנה">−</button>
      <span>{Math.round(scale * 100)}%</span>
      <button type="button" className="ghost" onClick={() => onZoom(clampScale(scale * 1.25))} aria-label="הגדלה">+</button>
      <button type="button" className="ghost" onClick={onReset}>איפוס</button>
      {painting ? <PaintTools tool={tool} width={width} onTool={onTool} onWidth={onWidth} /> : null}
    </div>
  );
}

function PaintTools({
  tool,
  width,
  onTool,
  onWidth,
}: {
  tool: "paint" | "pan";
  width: number;
  onTool: (tool: "paint" | "pan") => void;
  onWidth: (width: number) => void;
}) {
  return (
    <>
      <button type="button" className={tool === "paint" ? "chip active" : "chip"} onClick={() => onTool("paint")}>צביעה</button>
      <button type="button" className={tool === "pan" ? "chip active" : "chip"} onClick={() => onTool("pan")}>הזזה</button>
      <button type="button" className={width === 2 ? "chip active" : "chip"} onClick={() => onWidth(2)}>דק</button>
      <button type="button" className={width === 3.5 ? "chip active" : "chip"} onClick={() => onWidth(3.5)}>רגיל</button>
      <button type="button" className={width === 5.5 ? "chip active" : "chip"} onClick={() => onWidth(5.5)}>רחב</button>
    </>
  );
}

function startPointer(
  event: PointerEvent<HTMLDivElement>,
  drag: MutableRefObject<DragState | null>,
  offset: { x: number; y: number },
  painting: boolean,
  onDraft?: (points: PlanPoint[] | null) => void,
) {
  if (event.button !== 0) {
    return;
  }
  const point = percentOnImage(event, event.currentTarget);
  const points = painting && point !== null ? [point] : [];
  drag.current = { x: event.clientX, y: event.clientY, ox: offset.x, oy: offset.y, moved: false, points };
  event.currentTarget.setPointerCapture(event.pointerId);
  if (painting) {
    onDraft?.(points);
  }
}

function movePointer(
  event: PointerEvent<HTMLDivElement>,
  drag: MutableRefObject<DragState | null>,
  painting: boolean,
  setOffset: (offset: { x: number; y: number }) => void,
  onDraft?: (points: PlanPoint[] | null) => void,
) {
  const state = drag.current;
  if (state === null) {
    return;
  }
  const dx = event.clientX - state.x;
  const dy = event.clientY - state.y;
  if (Math.hypot(dx, dy) > 4) {
    state.moved = true;
  }
  if (painting) {
    appendPaintPoint(event, state, onDraft);
    return;
  }
  if (state.moved) {
    setOffset({ x: state.ox + dx, y: state.oy + dy });
  }
}

function appendPaintPoint(
  event: PointerEvent<HTMLDivElement>,
  state: DragState,
  onDraft?: (points: PlanPoint[] | null) => void,
) {
  const point = percentOnImage(event, event.currentTarget);
  if (point === null) {
    return;
  }
  const last = state.points[state.points.length - 1];
  if (last !== undefined && Math.hypot(point.x - last.x, point.y - last.y) < SAMPLE_GAP) {
    return;
  }
  state.points = [...state.points, point];
  onDraft?.(state.points);
}

function endPointer(
  drag: MutableRefObject<DragState | null>,
  painting: boolean,
  width: number,
  onPaint?: (points: PlanPoint[], width: number) => void,
  onDraft?: (points: PlanPoint[] | null) => void,
) {
  const state = drag.current;
  drag.current = null;
  onDraft?.(null);
  if (!painting || !onPaint || state === null || state.points.length === 0) {
    return;
  }
  onPaint(state.points, width);
}

function cancelPointer(drag: MutableRefObject<DragState | null>, onDraft?: (points: PlanPoint[] | null) => void) {
  drag.current = null;
  onDraft?.(null);
}

function useWheelZoom(
  stageRef: RefObject<HTMLDivElement | null>,
  scale: number,
  offset: { x: number; y: number },
  setScale: (scale: number) => void,
  setOffset: (offset: { x: number; y: number }) => void,
) {
  const view = useRef({ scale, offset });
  view.current = { scale, offset };
  useEffect(() => {
    const node = stageRef.current;
    if (node === null) {
      return;
    }
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const next = zoomToward(event, node, view.current.scale, view.current.offset);
      setScale(next.scale);
      setOffset(next.offset);
    };
    node.addEventListener("wheel", onWheel, { passive: false });
    return () => node.removeEventListener("wheel", onWheel);
  }, [setOffset, setScale, stageRef]);
}

function zoomToward(event: WheelEvent, node: HTMLDivElement, scale: number, offset: { x: number; y: number }) {
  const nextScale = clampScale(scale * (event.deltaY < 0 ? 1.15 : 1 / 1.15));
  const box = node.getBoundingClientRect();
  const cx = event.clientX - box.left;
  const cy = event.clientY - box.top;
  const ratio = nextScale / scale;
  return { scale: nextScale, offset: { x: cx - (cx - offset.x) * ratio, y: cy - (cy - offset.y) * ratio } };
}

function percentOnImage(event: PointerEvent<HTMLDivElement>, stage: HTMLDivElement): PlanPoint | null {
  const image = stage.querySelector("img");
  if (image === null) {
    return null;
  }
  const box = image.getBoundingClientRect();
  if (box.width === 0 || box.height === 0) {
    return null;
  }
  return {
    x: clampPercent(((event.clientX - box.left) / box.width) * 100),
    y: clampPercent(((event.clientY - box.top) / box.height) * 100),
  };
}

function stageClass(placing?: boolean, painting?: boolean): string {
  return ["plan-stage", placing ? "placing" : "", painting ? "painting" : ""].filter(Boolean).join(" ");
}

function resetView(setScale: (scale: number) => void, setOffset: (offset: { x: number; y: number }) => void) {
  setScale(1);
  setOffset({ x: 0, y: 0 });
}

function clampScale(value: number): number {
  return Math.min(MAX_SCALE, Math.max(MIN_SCALE, value));
}

function clampPercent(value: number): number {
  return Math.min(100, Math.max(0, value));
}
