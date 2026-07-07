import Link from "next/link";
import { dateHr } from "@/lib/personalize";

interface IssueHeroProps {
  issueDate: string;
  title?: string | null;
  intro?: string | null;
  readingMinutes?: number | null;
  editionHref?: string;
}

export function IssueHero({
  issueDate,
  title,
  intro,
  readingMinutes,
  editionHref,
}: IssueHeroProps) {
  return (
    <section className="hero-panel mb-10">
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span className="meta-pill">{dateHr(issueDate)}</span>
        {readingMinutes && (
          <span className="meta-pill meta-pill--accent">☕ {readingMinutes} min čitanja</span>
        )}
      </div>
      {title && (
        <h1 className="font-serif text-2xl md:text-[1.75rem] font-bold text-espresso leading-tight mb-4">
          {title}
        </h1>
      )}
      {intro && <p className="text-[1.05rem] md:text-lg leading-relaxed text-ink/90 max-w-2xl">{intro}</p>}
      {editionHref && (
        <Link href={editionHref} className="inline-flex items-center gap-1 mt-5 text-sm font-semibold text-espresso hover:text-sun transition-colors">
          Otvori cijelo izdanje
          <span aria-hidden>→</span>
        </Link>
      )}
    </section>
  );
}
