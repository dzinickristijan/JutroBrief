import Link from "next/link";
import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { dateHr } from "@/lib/personalize";
import { FavoriteButton } from "@/components/FavoriteButton";
import { RecordRead } from "@/components/RecordRead";

export default async function StoryPage({
  params,
}: {
  params: Promise<{ date: string; slug: string }>;
}) {
  const { date, slug } = await params;
  const supabase = await createClient();

  const { data: edition } = await supabase
    .from("editions")
    .select("id, issue_date, title")
    .eq("issue_date", date)
    .not("published_at", "is", null)
    .maybeSingle();

  if (!edition) notFound();

  const { data: story } = await supabase
    .from("stories")
    .select("*")
    .eq("edition_id", edition.id)
    .eq("slug", slug)
    .maybeSingle();

  if (!story) notFound();

  return (
    <main>
      <RecordRead editionId={edition.id} storyId={story.id} />
      <article className="story-article">
        <div className="flex flex-wrap gap-2 mb-3">
          <span className="meta-pill">{dateHr(date)}</span>
          <span className="meta-pill">{story.section_label}</span>
        </div>
        <h1 className="story-article__title">{story.title}</h1>
        <div className="story-article__body">
          {story.summary.split(/(?<=[.!?])\s+/).map((para: string, i: number) => (
            <p key={i}>{para}</p>
          ))}
        </div>
        {story.extended_body && (
          <div className="mt-6 pl-4 border-l-4 border-sun">
            <h2 className="font-serif text-lg font-semibold mb-2 text-espresso">Više konteksta</h2>
            <p className="text-ink/90 leading-relaxed">{story.extended_body}</p>
          </div>
        )}
        <div className="story-actions">
          <FavoriteButton storyId={story.id} />
          <a
            href={story.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="source-cta"
          >
            Pročitaj izvorni članak ↗
          </a>
        </div>
      </article>

      <div className="mt-8 flex flex-wrap gap-4 text-sm">
        <Link href={`/izdanje/${date}`} className="text-muted hover:text-ink">
          ← Natrag na izdanje
        </Link>
        <Link href="/" className="text-muted hover:text-ink">
          Početna
        </Link>
      </div>
    </main>
  );
}
