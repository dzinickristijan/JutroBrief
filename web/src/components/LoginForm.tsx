"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

interface Props {
  error?: string | null;
}

const COOLDOWN_SEC = 60;

function friendlyAuthError(message: string, status?: number): string {
  const lower = message.toLowerCase();
  if (lower.includes("rate limit") || lower.includes("too many")) {
    return "Dosegnut je limit slanja emailova. Pričekaj sat vremena ili koristi link iz ranijeg emaila.";
  }
  if (lower.includes("60 seconds") || lower.includes("once every")) {
    return "Pričekaj minutu prije slanja novog linka na isti email.";
  }
  if (
    status === 500 ||
    lower.includes("error sending") ||
    lower.includes("authentication credentials") ||
    lower.includes("smtp")
  ) {
    return "Email nije poslan — SMTP postavke u Supabaseu nisu ispravne. Provjeri Resend API ključ (host smtp.resend.com, user resend, port 465).";
  }
  if (!message.trim() || message === "{}") {
    return "Prijava nije uspjela (nepoznata greška). Otvori DevTools → Network i provjeri odgovor na /otp.";
  }
  return message;
}

export function LoginForm({ error }: Props) {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (cooldown > 0) return;

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
      setMsg(friendlyAuthError(authError.message, authError.status));
      if (authError.status === 429) setCooldown(COOLDOWN_SEC);
      return;
    }

    setSent(true);
    setCooldown(COOLDOWN_SEC);
    setMsgType("ok");
    setMsg("Link za prijavu je poslan. Provjeri inbox (i spam).");
  }

  const submitDisabled = loading || cooldown > 0;

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
            <p className="auth-hint mt-2 mb-0">
              Link vrijedi kratko — ako ne stigne novi email, provjeri spam ili pričekaj sat
              (limit testiranja na besplatnom Supabase emailu).
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
            <button type="submit" disabled={submitDisabled} className="auth-submit">
              {loading
                ? "Šaljem link…"
                : cooldown > 0
                  ? `Pričekaj ${cooldown}s`
                  : "Pošalji link za prijavu"}
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
