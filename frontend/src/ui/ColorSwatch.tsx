import { dedicationSolid } from "./dedicationTint";

export function ColorSwatch({ dedicationId }: { dedicationId: string }) {
  return <span className="color-swatch" style={{ background: dedicationSolid(dedicationId) }} aria-hidden />;
}
