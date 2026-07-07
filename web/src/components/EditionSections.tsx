import type { StoryGroup } from "@/lib/personalize";
import { StoryCard } from "./StoryCard";
import { CATEGORY_LABELS } from "@/lib/types";

interface EditionSectionsProps {
  featured: StoryGroup[];
  collapsed: StoryGroup[];
  date: string;
}

export function EditionSections({ featured, collapsed, date }: EditionSectionsProps) {
  return (
    <div className="edition-sections">
      {featured.map((group) => (
        <section key={group.category} className="category-block">
          <div className="category-block__head">
            <h2 className="category-block__title">
              {CATEGORY_LABELS[group.category] || group.label}
            </h2>
            <span className="category-block__count">{group.stories.length} priča</span>
          </div>
          <div className="category-block__stories">
            {group.stories.map((story) => (
              <StoryCard key={story.id} story={story} date={date} />
            ))}
          </div>
        </section>
      ))}

      {collapsed.length > 0 && (
        <div className="collapsed-wrap">
          {collapsed.map((group) => (
            <details key={group.category} className="collapsed-panel">
              <summary className="collapsed-panel__summary">
                <span>{CATEGORY_LABELS[group.category] || group.label}</span>
                <span className="collapsed-panel__badge">
                  {group.stories.length} {group.stories.length === 1 ? "priča" : "priče"}
                </span>
              </summary>
              <div className="collapsed-panel__body">
                {group.stories.map((story) => (
                  <StoryCard key={story.id} story={story} date={date} variant="compact" />
                ))}
              </div>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
