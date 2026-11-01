import type { Dedication } from "../api";

export function dedicationHue(id: string): number {
  let hash = 2166136261;
  for (const char of id) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) % 360;
}

export function dedicationSolid(id: string): string {
  return `hsl(${dedicationHue(id)} 58% 44%)`;
}

export function dedicationFill(id: string, status: Dedication["status"]): string {
  const opacity = status === "realized" ? 0.58 : status === "fundraising" ? 0.5 : 0.42;
  return `hsla(${dedicationHue(id)} 62% 46% / ${opacity})`;
}

export function dedicationStroke(id: string): string {
  return `hsl(${dedicationHue(id)} 62% 34%)`;
}
