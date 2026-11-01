import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import {
  deleteGalleryImage,
  getPublicPageSettings,
  listGallery,
  savePublicPageSettings,
  uploadGalleryImage,
  type PublicPageSettings,
} from "../../api";
import type { Session } from "../../session";
import { useAuthorizedImage } from "./usePlanUrl";

type Draft = { slug: string; vision: string; enabled: boolean };

export function PublicPagePanel({ session, projectId }: { session: Session; projectId: string }) {
  const [settings, setSettings] = useState<PublicPageSettings | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getPublicPageSettings(session, projectId)
      .then((value) => {
        setSettings(value);
        setLoaded(true);
      })
      .catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "הפעולה נכשלה"));
  }, [session, projectId]);

  return (
    <section className="workspace">
      <h2 className="section-title">עמוד ציבורי</h2>
      <p className="muted">
        עמוד לתורמים ולקהילה, בלי כניסה למערכת: חזון הפרויקט, גלריה, מפת החום וההקדשות עם הסטטוס והמחיר.
      </p>
      <PublicLinkCard settings={settings} />
      {error ? <p className="error">{error}</p> : null}
      {loaded ? (
        <SettingsForm session={session} projectId={projectId} settings={settings} onSaved={setSettings} />
      ) : null}
      <Gallery session={session} projectId={projectId} />
    </section>
  );
}

function PublicLinkCard({ settings }: { settings: PublicPageSettings | null }) {
  const [copied, setCopied] = useState(false);
  if (settings === null) {
    return null;
  }
  const url = `${window.location.origin}/p/${settings.slug}`;
  const copy = () => {
    void navigator.clipboard.writeText(url).then(() => setCopied(true));
  };
  return (
    <div className={settings.enabled ? "public-link live" : "public-link"}>
      <span className="eyebrow">{settings.enabled ? "העמוד פעיל" : "העמוד כבוי"}</span>
      <a href={url} target="_blank" rel="noreferrer" dir="ltr">{url}</a>
      <button type="button" className="ghost" onClick={copy}>{copied ? "הקישור הועתק" : "העתקת הקישור"}</button>
    </div>
  );
}

function SettingsForm({
  session,
  projectId,
  settings,
  onSaved,
}: {
  session: Session;
  projectId: string;
  settings: PublicPageSettings | null;
  onSaved: (settings: PublicPageSettings) => void;
}) {
  const [draft, setDraft] = useState<Draft>(toDraft(settings));
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => setDraft(toDraft(settings)), [settings]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      onSaved(await savePublicPageSettings(session, projectId, draft));
      setError("");
      setSaved(true);
    } catch (caught) {
      setSaved(false);
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  return (
    <form className="panel" onSubmit={submit}>
      <label>
        כתובת העמוד (אותיות לטיניות, ספרות ומקפים)
        <input
          value={draft.slug}
          dir="ltr"
          placeholder="tiferet-tzvi"
          onChange={(event) => setDraft({ ...draft, slug: event.target.value })}
          required
        />
      </label>
      <label>
        חזון הפרויקט
        <textarea
          value={draft.vision}
          rows={5}
          maxLength={2000}
          placeholder="מה בונים, למי, ולמה זה חשוב לקהילה."
          onChange={(event) => setDraft({ ...draft, vision: event.target.value })}
        />
      </label>
      <label className="check">
        <input
          type="checkbox"
          checked={draft.enabled}
          onChange={(event) => setDraft({ ...draft, enabled: event.target.checked })}
        />
        העמוד פתוח לציבור
      </label>
      {error ? <p className="error">{error}</p> : null}
      <div className="row">
        <button type="submit">שמירה</button>
        {saved ? <span className="muted">נשמר.</span> : null}
      </div>
    </form>
  );
}

function Gallery({ session, projectId }: { session: Session; projectId: string }) {
  const [imageIds, setImageIds] = useState<string[]>([]);
  const [error, setError] = useState("");

  const reload = () => {
    listGallery(session, projectId)
      .then(setImageIds)
      .catch((caught: unknown) => setError(caught instanceof Error ? caught.message : "הפעולה נכשלה"));
  };

  useEffect(reload, [session, projectId]);

  async function remove(imageId: string) {
    try {
      await deleteGalleryImage(session, imageId);
      setError("");
      reload();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  return (
    <div className="workspace">
      <h3>גלריה</h3>
      <p className="muted">הדמיות ותמונות של הפרויקט, עד 12 תמונות. PNG, JPEG או WebP.</p>
      {error ? <p className="error">{error}</p> : null}
      {imageIds.length > 0 ? (
        <div className="gallery">
          {imageIds.map((imageId) => (
            <GalleryThumb key={imageId} session={session} imageId={imageId} onRemove={() => void remove(imageId)} />
          ))}
        </div>
      ) : null}
      <label className="file-button">
        הוספת תמונה
        <input
          type="file"
          accept="image/png,image/jpeg,image/webp"
          onChange={(event) => void upload(event, session, projectId, reload, setError)}
        />
      </label>
    </div>
  );
}

function GalleryThumb({ session, imageId, onRemove }: { session: Session; imageId: string; onRemove: () => void }) {
  const image = useAuthorizedImage(session, `/api/gallery/${imageId}`, 0);
  return (
    <figure className="gallery-item">
      {image.url ? <img src={image.url} alt="" /> : <span className="gallery-placeholder" />}
      <button type="button" className="ghost" onClick={onRemove} aria-label="הסרת התמונה">×</button>
    </figure>
  );
}

function toDraft(settings: PublicPageSettings | null): Draft {
  return settings
    ? { slug: settings.slug, vision: settings.vision, enabled: settings.enabled }
    : { slug: "", vision: "", enabled: false };
}

async function upload(
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
    await uploadGalleryImage(session, projectId, file);
    onError("");
    onUploaded();
  } catch (caught) {
    onError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
  }
}
