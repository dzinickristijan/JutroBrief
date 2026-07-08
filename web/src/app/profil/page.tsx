import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { redirectAuthParamsIfPresent } from "@/lib/auth-redirect";
import { PreferencesForm } from "@/components/PreferencesForm";
import { FavoritesList } from "@/components/FavoritesList";
import { dateHr } from "@/lib/personalize";
import type { UserPreferences } from "@/lib/types";

function userInitial(email: string): string {
  return (email[0] ?? "?").toUpperCase();
}

export default async function ProfilePage({
  searchParams,
}: {
  searchParams: Promise<{ code?: string; token_hash?: string; type?: string }>;
}) {
  const params = await searchParams;
  redirectAuthParamsIfPresent(params, "/profil");

  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect("/prijava");
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("display_name, created_at")
    .eq("id", user.id)
    .maybeSingle();

  const { data: prefs } = await supabase
    .from("user_preferences")
    .select("category_weights, collapsed_categories")
    .eq("user_id", user.id)
    .maybeSingle();

  const { data: history } = await supabase
    .from("reading_history")
    .select("read_at, story_id, editions(issue_date, title), stories(title, slug)")
    .eq("user_id", user.id)
    .order("read_at", { ascending: false })
    .limit(15);

  const { data: favorites } = await supabase
    .from("favorites")
    .select("story_id, stories(id, title, slug, editions(issue_date))")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false })
    .limit(20);

  const initial: UserPreferences = {
    category_weights: prefs?.category_weights ?? {
      hr: 3, svijet: 2, biznis: 2, sport: 1, za_kraj: 1,
    },
    collapsed_categories: prefs?.collapsed_categories ?? ["sport"],
  };

  const favoriteItems = (favorites ?? [])
    .map((f) => {
      const st = f.stories as unknown as {
        id: string;
        title: string;
        slug: string;
        editions: { issue_date: string } | null;
      } | null;
      if (!st?.editions) return null;
      return {
        storyId: st.id,
        title: st.title,
        slug: st.slug,
        issueDate: st.editions.issue_date,
      };
    })
    .filter(Boolean) as {
    storyId: string;
    title: string;
    slug: string;
    issueDate: string;
  }[];

  const displayName = profile?.display_name || user.email?.split("@")[0] || "Čitatelj";

  return (
    <main className="profile-page">
      <section className="profile-hero">
        <div className="profile-hero__avatar">{userInitial(user.email ?? "?")}</div>
        <div>
          <h1 className="profile-hero__name">{displayName}</h1>
          <p className="profile-hero__email">{user.email}</p>
          {profile?.created_at && (
            <p className="profile-hero__since">
              Čitatelj od {dateHr(profile.created_at.slice(0, 10))}
            </p>
          )}
        </div>
        <form action="/auth/signout" method="post" className="profile-hero__logout">
          <button type="submit" className="profile-logout-btn">
            Odjava
          </button>
        </form>
      </section>

      <section className="profile-section">
        <h2 className="profile-section__title">Postavke rubrika</h2>
        <p className="profile-section__desc">
          Tvoj brief na početnoj prilagođava se ovim postavkama — ista izdanja, drugačiji raspored.
        </p>
        <PreferencesForm userId={user.id} initial={initial} />
      </section>

      <section className="profile-section">
        <h2 className="profile-section__title">Favoriti</h2>
        <FavoritesList items={favoriteItems} />
      </section>

      <section className="profile-section">
        <h2 className="profile-section__title">Povijest čitanja</h2>
        {history?.length ? (
          <ul className="profile-list">
            {history.map((h, i) => {
              const ed = h.editions as unknown as { issue_date: string; title: string } | null;
              const st = h.stories as unknown as { title: string; slug: string } | null;
              if (!ed) return null;
              return (
                <li key={i} className="profile-list__item profile-list__item--static">
                  <div className="profile-list__main">
                    {st ? (
                      <Link
                        href={`/prica/${ed.issue_date}/${st.slug}`}
                        className="profile-list__link"
                      >
                        {st.title}
                      </Link>
                    ) : (
                      <Link href={`/izdanje/${ed.issue_date}`} className="profile-list__link">
                        Izdanje — {dateHr(ed.issue_date)}
                      </Link>
                    )}
                    <span className="profile-list__meta">
                      {new Date(h.read_at).toLocaleDateString("hr-HR", {
                        day: "numeric",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="profile-empty">
            Još nema zabilježenog čitanja. Otvori neku priču dok si prijavljen.
          </p>
        )}
      </section>

      <div className="profile-cta">
        <Link href="/" className="source-cta">
          Vidi današnji brief
        </Link>
      </div>
    </main>
  );
}
