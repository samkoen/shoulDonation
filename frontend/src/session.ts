export type Role = "platform_admin" | "lead_projector" | "sub_projector";

export type Session = {
  accessToken: string;
  userId: string;
  role: Role;
  synagogueId: string | null;
};

export type Synagogue = {
  id: string;
  name: string;
};

export type Project = {
  id: string;
  synagogueId: string;
  name: string;
};

const storageKey = "shoul.session";

export function readSession(): Session | null {
  const raw = sessionStorage.getItem(storageKey);
  if (raw === null) {
    return null;
  }
  return JSON.parse(raw) as Session;
}

export function storeSession(session: Session): void {
  sessionStorage.setItem(storageKey, JSON.stringify(session));
}

export function clearSession(): void {
  sessionStorage.removeItem(storageKey);
}
