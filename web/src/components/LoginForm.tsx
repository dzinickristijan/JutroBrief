"use client";

import Link from "next/link";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";

interface Props {
  error?: string | null;
}

export function LoginForm({ error }: Props) {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    const supabase = createClient();
    const redirectTo = `${window.location.origin}/auth/callback?next=/profil`;
    const { error: authError } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: redirectTo },
    });
    setLoading(false);
    if (authError) {
      setMsgType("err");
      setMsg(authError.message);
      return;
    }
    setSent(true);
    setMsgType("ok");
    setMsg("Link za prijavu je poslan. Provjeri inbox (i spam).");
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-card__icon">☕</div>
        <h1 className="auth-card__title">Prijava</h1>
        <p className="auth-card__lead">
          Bez lozinke — šaljemo ti magic link na email. Jedan klik i brief je personaliziran.
        </p>

        <ul className="auth-benefits">
          <li>Rubrike po tvom ukusu (više HR, manje sporta…)</li>
          <li>Arhiva svih izdanja na jednom mjestu</li>
          <li>Favoriti i povijest čitanja</li>
        </ul>

        {error && (
          <div className="auth-alert auth-alert--error">
            Prijava nije uspjela. Pokušaj ponovo.
          </div>
        )}

        {sent ? (
          <div className="auth-alert auth-alert--ok">
            <strong>Provjeri email.</strong>
            <p className="mt-1 mb-0">
              Poslali smo link na <strong>{email}</strong>. Klikni ga da završiš prijavu.
            </p>
          </div>
        ) : (
          <form onSubmit={handleLogin} className="auth-form">
            <label className="auth-label" htmlFor="email">
              Email adresa
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              placeholder="tvoj@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="auth-input"
            />
            <button type="submit" disabled={loading} className="auth-submit">
              {loading ? "Šaljem link…" : "Pošalji link za prijavu"}
            </button>
          </form>
        )}

        {msg && !sent && (
          <div className={`auth-alert auth-alert--${msgType === "err" ? "error" : "ok"}`}>
            {msg}
          </div>
        )}

        <Link href="/" className="auth-back">
          ← Natrag na početnu
        </Link>
      </div>
    </div>
  );
}
