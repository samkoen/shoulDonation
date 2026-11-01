import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { roleLabels } from "../ui/labels";
import { useRequiredSession } from "../session/SessionProvider";

export function Shell({ children }: { children: ReactNode }) {
  const { session, signOut } = useRequiredSession();
  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">גיוס לבתי כנסת</Link>
        <div className="topbar-actions">
          <span className="role-pill">{roleLabels[session.role]}</span>
          <button type="button" className="ghost" onClick={signOut}>יציאה</button>
        </div>
      </header>
      <main className="page">{children}</main>
    </div>
  );
}
