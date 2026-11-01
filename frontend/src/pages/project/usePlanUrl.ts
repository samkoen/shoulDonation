import { useEffect, useState } from "react";
import { fetchImage } from "../../api";
import type { Session } from "../../session";

export type PlanState = { url: string | null; loaded: boolean; error: string };

export function usePlanUrl(session: Session, projectId: string, version: number): PlanState {
  return useAuthorizedImage(session, `/api/projects/${projectId}/plan`, version);
}

/** Loads a protected image into an object URL, so an <img> can show it without a token. */
export function useAuthorizedImage(session: Session, path: string, version: number): PlanState {
  const [state, setState] = useState<PlanState>({ url: null, loaded: false, error: "" });

  useEffect(() => {
    let active = true;
    let current: string | null = null;
    fetchImage(session, path)
      .then((url) => {
        if (!active) {
          revoke(url);
          return;
        }
        current = url;
        setState({ url, loaded: true, error: "" });
      })
      .catch((caught: unknown) => {
        if (active) {
          setState({ url: null, loaded: true, error: caught instanceof Error ? caught.message : "הפעולה נכשלה" });
        }
      });
    return () => {
      active = false;
      revoke(current);
    };
  }, [session, path, version]);

  return state;
}

function revoke(url: string | null): void {
  if (url) {
    URL.revokeObjectURL(url);
  }
}
