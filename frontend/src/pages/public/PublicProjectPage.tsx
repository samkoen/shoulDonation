import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchPublicProject, publicGalleryUrl, publicPlanUrl, type Dedication, type PublicProject } from "../../api";
import { ColorSwatch } from "../../ui/ColorSwatch";
import { statusLabels } from "../../ui/labels";
import { PlanCanvas } from "../project/PlanCanvas";
import { ContactForm } from "./ContactForm";

type LoadState = { project: PublicProject | null; loaded: boolean; error: string };

export function PublicProjectPage() {
  const { slug } = useParams();
  const [state, setState] = useState<LoadState>({ project: null, loaded: false, error: "" });

  useEffect(() => {
    if (slug === undefined) {
      return;
    }
    fetchPublicProject(slug)
      .then((project) => setState({ project, loaded: true, error: "" }))
      .catch((caught: unknown) =>
        setState({ project: null, loaded: true, error: caught instanceof Error ? caught.message : "הפעולה נכשלה" }),
      );
  }, [slug]);

  return (
    <div className="shell public">
      <header className="topbar">
        <span className="brand">גיוס לבתי כנסת</span>
      </header>
      <main className="page">
        {state.error ? <p className="error">{state.error}</p> : null}
        {state.loaded && state.project === null && !state.error ? <MissingPage /> : null}
        {state.project ? <ProjectShowcase project={state.project} /> : null}
      </main>
    </div>
  );
}

function MissingPage() {
  return (
    <section className="public-hero">
      <h1>העמוד לא נמצא</h1>
      <p className="muted">ייתכן שהכתובת השתנתה או שהעמוד עדיין לא נפתח לציבור.</p>
    </section>
  );
}

function ProjectShowcase({ project }: { project: PublicProject }) {
  const [selected, setSelected] = useState<Dedication | null>(null);
  return (
    <>
      <Hero project={project} />
      <Gallery project={project} />
      {project.hasPlan ? (
        <PublicHeatmap project={project} selected={selected} onSelect={setSelected} />
      ) : null}
      <DedicationList project={project} selected={selected} onSelect={setSelected} />
      <section className="workspace" id="contact">
        <h2 className="section-title">יצירת קשר</h2>
        <p className="muted">השאירו פרטים ונחזור אליכם. אפשר לציין הקדשה אם כבר בחרתם אחת במפה.</p>
        <ContactForm slug={project.slug} />
      </section>
    </>
  );
}

function Hero({ project }: { project: PublicProject }) {
  const summary = statusSummary(project.dedications);
  return (
    <section className="public-hero">
      <p className="eyebrow">{project.synagogueName}</p>
      <h1>{project.projectName}</h1>
      {project.vision ? <p className="vision">{project.vision}</p> : (
        <p className="muted">פרויקט גיוס להקדשות בית הכנסת. בחרו הקדשה במפה או ברשימה.</p>
      )}
      <div className="legend">
        {summary.map(([status, count]) => (
          <span key={status} className={`legend-item status-${status}`}>{statusLabels[status]} · {count}</span>
        ))}
      </div>
      <div className="row">
        {project.hasPlan ? <a className="action-link" href="#heatmap">למפת ההקדשות</a> : null}
        <a className="action-link" href="#contact">יצירת קשר</a>
      </div>
    </section>
  );
}

function Gallery({ project }: { project: PublicProject }) {
  if (project.galleryImageIds.length === 0) {
    return null;
  }
  return (
    <section className="gallery public-gallery">
      {project.galleryImageIds.map((imageId) => (
        <figure key={imageId} className="gallery-item">
          <img src={publicGalleryUrl(project.slug, imageId)} alt="" loading="lazy" />
        </figure>
      ))}
    </section>
  );
}

function PublicHeatmap({
  project,
  selected,
  onSelect,
}: {
  project: PublicProject;
  selected: Dedication | null;
  onSelect: (dedication: Dedication) => void;
}) {
  return (
    <section className="workspace heatmap-block" id="heatmap">
      <h2 className="section-title">מפת ההקדשות</h2>
      <p className="muted">לחצו על אזור בתוכנית או על שורה ברשימה. הצבע זהה בשני המקומות.</p>
      <div className="heatmap-split">
        <PlanCanvas
          url={publicPlanUrl(project.slug)}
          dedications={project.dedications}
          activeId={selected?.id}
          onMarkerClick={onSelect}
        />
        {selected ? <SelectedDedication dedication={selected} currency={project.currency} /> : (
          <p className="empty">בחרו הקדשה במפה כדי לראות מחיר וסטטוס.</p>
        )}
      </div>
    </section>
  );
}

function SelectedDedication({ dedication, currency }: { dedication: Dedication; currency: string }) {
  return (
    <article className={`dedication status-${dedication.status}`}>
      <span className="eyebrow">{statusLabels[dedication.status]}</span>
      <strong>{dedication.name}</strong>
      <p className="amount">{dedication.price} <small>{currency}</small></p>
      <a href="#contact" className="action-link">מעוניינים? צרו קשר</a>
    </article>
  );
}

function DedicationList({
  project,
  selected,
  onSelect,
}: {
  project: PublicProject;
  selected: Dedication | null;
  onSelect: (dedication: Dedication) => void;
}) {
  if (project.dedications.length === 0) {
    return null;
  }
  return (
    <section className="workspace">
      <h2 className="section-title">ההקדשות</h2>
      <div className="catalog">
        {project.dedications.map((dedication) => (
          <button
            key={dedication.id}
            type="button"
            className={`catalog-row status-${dedication.status}${selected?.id === dedication.id ? " selected" : ""}`}
            onClick={() => onSelect(dedication)}
          >
            <ColorSwatch dedicationId={dedication.id} />
            <span className="eyebrow">{statusLabels[dedication.status]}</span>
            <span className="catalog-name">{dedication.name}</span>
            <strong className="catalog-price">{dedication.price} {project.currency}</strong>
          </button>
        ))}
      </div>
    </section>
  );
}

function statusSummary(dedications: Dedication[]): Array<[Dedication["status"], number]> {
  const order: Dedication["status"][] = ["open", "fundraising", "realized"];
  return order.map((status) => [status, dedications.filter((item) => item.status === status).length]);
}
