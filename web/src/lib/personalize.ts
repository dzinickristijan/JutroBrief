import type { Story, StoryCategory, CategoryWeights, UserPreferences } from "./types";
import { DEFAULT_WEIGHTS } from "./types";

export interface StoryGroup {
  category: StoryCategory;
  label: string;
  stories: Story[];
  collapsed: boolean;
}

const CATEGORY_ORDER: StoryCategory[] = ["hr", "svijet", "biznis", "sport", "za_kraj"];

/** Personalizirani prikaz: rubrike po težini, slabe/sklopive na dno. */
export function groupStoriesForReader(
  stories: Story[],
  prefs?: Partial<UserPreferences> | null,
): { featured: StoryGroup[]; collapsed: StoryGroup[] } {
  const weights = { ...DEFAULT_WEIGHTS, ...(prefs?.category_weights ?? {}) };
  const collapsedSet = new Set(prefs?.collapsed_categories ?? ["sport"]);

  const byCategory = new Map<StoryCategory, Story[]>();
  for (const cat of CATEGORY_ORDER) {
    byCategory.set(cat, []);
  }
  for (const story of stories) {
    byCategory.get(story.category)?.push(story);
  }

  const groups: StoryGroup[] = CATEGORY_ORDER.map((category) => ({
    category,
    label: stories.find((s) => s.category === category)?.section_label || category,
    stories: byCategory.get(category) ?? [],
    collapsed: collapsedSet.has(category),
  })).filter((g) => g.stories.length > 0);

  // Viša težina = više priča na vrhu unutar prioriteta rubrike
  for (const group of groups) {
    const limit = Math.min(group.stories.length, Math.max(1, weights[group.category]));
    if (weights[group.category] >= 3 && group.stories.length > limit) {
      // Za visoki prioritet (npr. HR=5) prikaži sve priče te rubrike
      if (weights[group.category] >= 4) continue;
    }
  }

  const sortKey = (g: StoryGroup) => weights[g.category] ?? 0;
  const expanded = groups.filter((g) => !g.collapsed).sort((a, b) => sortKey(b) - sortKey(a));
  const collapsed = groups.filter((g) => g.collapsed).sort((a, b) => sortKey(b) - sortKey(a));

  // za_kraj uvijek prije sklopivih blokova
  const zaKrajIdx = expanded.findIndex((g) => g.category === "za_kraj");
  if (zaKrajIdx >= 0 && zaKrajIdx < expanded.length - 1) {
    const [zk] = expanded.splice(zaKrajIdx, 1);
    const insertAt = Math.max(0, expanded.length);
    expanded.splice(insertAt, 0, zk);
  }

  return { featured: expanded, collapsed };
}

export function dateHr(isoDate: string): string {
  const months = [
    "", "siječnja", "veljače", "ožujka", "travnja", "svibnja", "lipnja",
    "srpnja", "kolovoza", "rujna", "listopada", "studenoga", "prosinca",
  ];
  const d = new Date(isoDate + "T12:00:00");
  return `${d.getDate()}. ${months[d.getMonth() + 1]} ${d.getFullYear()}.`;
}
