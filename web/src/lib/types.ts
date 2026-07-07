export type StoryCategory = "hr" | "svijet" | "biznis" | "sport" | "za_kraj";

export type CategoryWeights = Record<StoryCategory, number>;

export interface Edition {
  id: string;
  issue_date: string;
  title: string;
  intro: string | null;
  closing: string | null;
  reading_minutes: number | null;
  published_at: string | null;
}

export interface Story {
  id: string;
  edition_id: string;
  category: StoryCategory;
  section_label: string;
  title: string;
  slug: string;
  summary: string;
  source_url: string;
  sort_order: number;
  extended_body: string | null;
}

export interface UserPreferences {
  category_weights: CategoryWeights;
  collapsed_categories: string[];
}

export const DEFAULT_WEIGHTS: CategoryWeights = {
  hr: 3,
  svijet: 2,
  biznis: 2,
  sport: 1,
  za_kraj: 1,
};

export const CATEGORY_LABELS: Record<StoryCategory, string> = {
  hr: "🇭🇷 Hrvatska",
  svijet: "🌍 Svijet",
  biznis: "💼 Biznis & Tech",
  sport: "⚽ Sport",
  za_kraj: "☕ Za kraj",
};
