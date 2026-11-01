import { createContext, useContext, type ReactNode, useState } from "react";
import { clearSession, readSession, storeSession, type Session } from "../session";

type AppSession = {
  session: Session | null;
  signIn: (session: Session) => void;
  signOut: () => void;
};

const AppSessionContext = createContext<AppSession | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(readSession());

  function signIn(next: Session) {
    storeSession(next);
    setSession(next);
  }

  function signOut() {
    clearSession();
    setSession(null);
  }

  return <AppSessionContext.Provider value={{ session, signIn, signOut }}>{children}</AppSessionContext.Provider>;
}

export function useAppSession(): AppSession {
  const value = useContext(AppSessionContext);
  if (value === null) {
    throw new Error("Session provider is missing");
  }
  return value;
}

export function useRequiredSession(): { session: Session; signOut: () => void } {
  const { session, signOut } = useAppSession();
  if (session === null) {
    throw new Error("Session is missing");
  }
  return { session, signOut };
}
