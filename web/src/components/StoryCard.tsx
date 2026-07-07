import Link from "next/link";
import type { Story } from "@/lib/types";

interface StoryCardProps {
  story: Story;
  date: string;
  variant?: "default" | "compact";
}

export function StoryCard({ story, date, variant = "default" }: StoryCardProps) {
  return (
    <article className={`story-card ${variant === "compact" ? "story-card--compact" : ""}`}>
      <h3 className="story-card__title">
        <Link href={`/prica/${date}/${story.slug}`}>{story.title}</Link>
      </h3>
      <p className="story-card__summary">{story.summary}</p>
      <div className="story-card__footer">
        <Link href={`/prica/${date}/${story.slug}`} className="story-card__more">
          Pročitaj više
        </Link>
        <a
          href={story.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="story-card__source"
        >
          Izvor ↗
        </a>
      </div>
    </article>
  );
}
