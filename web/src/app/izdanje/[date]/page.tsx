import Link from "next/link";
import { notFound } from "next/navigation";
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

export default async function EditionPage({
  params,
}: {
  params: Promise<{ date: string }>;
}) {
  const { date } = await params;
  const supabase = await createClient();

  const { data: edition } = await supabase
    .from("editions")
    .select("*")
    .eq("issue_date", date)
    .not("published_at", "is", null)
    .maybeSingle();

  if (!edition) notFound();

  const { data: stories } = await supabase
    .from("stories")
    .select("*")
    .eq("edition_id", edition.id)
    .order("sort_order");

  const { data: { user } } = await supabase.auth.getUser();
  let prefs: UserPreferences | null = null;
  if (user) {
    const { data } = await supabase
      .from("user_preferences")
      .select("category_weights, collapsed_categories")
      .eq("user_id", user.id)
      .maybeSingle();
    prefs = data as UserPreferences | null;
  }

  const { featured, collapsed } = groupStoriesForReader(
    (stories ?? []) as Story[],
    prefs,
  );

  return (
    <main>
      <IssueHero
        issueDate={date}
        title={edition.title}
        intro={edition.intro ? cleanIntro(edition.intro) : null}
        readingMinutes={edition.reading_minutes}
      />

      <EditionSections featured={featured} collapsed={collapsed} date={date} />

      {edition.closing && (
        <p className="mt-10 text-muted italic border-t border-line pt-6 text-center text-sm">
          {edition.closing}
        </p>
      )}

      <div className="mt-8">
        <Link href="/arhiva" className="text-muted hover:text-ink text-sm">
          ← Arhiva izdanja
        </Link>
      </div>
    </main>
  );
}
