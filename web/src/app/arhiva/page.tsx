import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { dateHr } from "@/lib/personalize";

export default async function ArchivePage() {
  const supabase = await createClient();
  const { data: editions } = await supabase
    .from("editions")
    .select("issue_date, title, reading_minutes")
    .not("published_at", "is", null)
    .order("issue_date", { ascending: false });

  return (
    <main>
      <h1 className="font-serif text-2xl font-bold mb-2 text-espresso">Arhiva</h1>
      <p className="text-muted text-sm mb-6">Sva objavljena jutarnja izdanja, po danima.</p>

      <ul className="archive-list">
        {(editions ?? []).map((e) => (
          <li key={e.issue_date} className="archive-item">
            <Link href={`/izdanje/${e.issue_date}`} className="archive-link">
              <span>Izdanje — {dateHr(e.issue_date)}</span>
              {e.reading_minutes && <span>☕ {e.reading_minutes} min</span>}
            </Link>
          </li>
        ))}
      </ul>

      {!editions?.length && (
        <p className="text-muted">Arhiva je prazna — sinkroniziraj izdanja u Supabase.</p>
      )}
    </main>
  );
}
