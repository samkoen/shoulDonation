import { Navigate, Outlet } from "react-router-dom";
import { useAppSession } from "../session/SessionProvider";

export function RequireSession() {
  const { session } = useAppSession();
  if (session === null) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
