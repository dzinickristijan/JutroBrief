import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { groupStoriesForReader } from "@/lib/personalize";
import { EditionSections } from "@/components/EditionSections";
import { IssueHero } from "@/components/IssueHero";
import type { Story, UserPreferences } from "@/lib/types";

function cleanIntro(intro: string): string {
  if (intro.includes("Dobro jutro")) {
    return intro.slice(intro.indexOf("Dobro jutro"));
  }
  return intro;
}

async function getLatestEdition() {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("editions")
    .select("*")
    .order("issue_date", { ascending: false })
    .limit(5);

  if (error) {
    console.error("Supabase editions error:", error.message);
    return null;
  }

  return data?.find((e) => e.published_at) ?? null;
}

async function getStories(editionId: string) {
  const supabase = await createClient();
  const { data } = await supabase
    .from("stories")
    .select("*")
    .eq("edition_id", editionId)
    .order("sort_order");
  return (data ?? []) as Story[];
}

async function getUserPrefs(userId: string): Promise<UserPreferences | null> {
  const supabase = await createClient();
  const { data } = await supabase
    .from("user_preferences")
    .select("category_weights, collapsed_categories")
    .eq("user_id", userId)
    .maybeSingle();
  return data as UserPreferences | null;
}

export default async function HomePage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  const edition = await getLatestEdition();

  if (!edition) {
    return (
      <main>
        <p className="text-muted">Još nema objavljenih izdanja. Pokreni push u Supabase.</p>
      </main>
    );
  }

  const stories = await getStories(edition.id);
  const prefs = user ? await getUserPrefs(user.id) : null;
  const { featured, collapsed } = groupStoriesForReader(stories, prefs);

  return (
    <main>
      <IssueHero
        issueDate={edition.issue_date}
        title={edition.title}
        intro={edition.intro ? cleanIntro(edition.intro) : null}
        readingMinutes={edition.reading_minutes}
        editionHref={`/izdanje/${edition.issue_date}`}
      />

      <EditionSections featured={featured} collapsed={collapsed} date={edition.issue_date} />

      <div className="mt-10 pt-6 border-t border-line text-center">
        <Link
          href={`/izdanje/${edition.issue_date}`}
          className="source-cta"
        >
          Cijelo današnje izdanje
        </Link>
      </div>
    </main>
  );
}
