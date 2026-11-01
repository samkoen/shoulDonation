import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { login } from "../api";
import { useAppSession } from "../session/SessionProvider";

export function LoginPage() {
  const { session, signIn } = useAppSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  if (session !== null) {
    return <Navigate to="/" replace />;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      signIn(await login(email, password));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "הפעולה נכשלה");
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={submit}>
        <p className="eyebrow">פלטפורמת גיוס</p>
        <h1>גיוס לבתי כנסת</h1>
        <label>
          דואר אלקטרוני
          <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
        </label>
        <label>
          סיסמה
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit">כניסה</button>
      </form>
    </div>
  );
}
