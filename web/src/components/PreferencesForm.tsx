"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import type { CategoryWeights, StoryCategory, UserPreferences } from "@/lib/types";
import { CATEGORY_LABELS, DEFAULT_WEIGHTS } from "@/lib/types";

const CATEGORIES: StoryCategory[] = ["hr", "svijet", "biznis", "sport", "za_kraj"];

const WEIGHT_LABELS = ["Isključeno", "Vrlo malo", "Malo", "Normalno", "Više", "Prioritet"];

interface Props {
  userId: string;
  initial: UserPreferences;
}

export function PreferencesForm({ userId, initial }: Props) {
  const [weights, setWeights] = useState<CategoryWeights>({
    ...DEFAULT_WEIGHTS,
    ...initial.category_weights,
  });
  const [collapsed, setCollapsed] = useState<string[]>(initial.collapsed_categories ?? ["sport"]);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    const supabase = createClient();
    const { error } = await supabase.from("user_preferences").upsert({
      user_id: userId,
      category_weights: weights,
      collapsed_categories: collapsed,
      updated_at: new Date().toISOString(),
    });
    setSaving(false);
    if (!error) {
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    }
  }

  function toggleCollapsed(cat: string) {
    setCollapsed((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat],
    );
  }

  return (
    <div className="prefs-form">
      <p className="prefs-form__hint">
        Podesi kako želiš čitati brief. Viša težina = rubrika ide prema vrhu. &quot;Sklopi&quot; =
        prikazuje se na dnu u expandable bloku.
      </p>

      <div className="prefs-grid">
        {CATEGORIES.map((cat) => (
          <div key={cat} className="prefs-card">
            <div className="prefs-card__head">
              <span className="prefs-card__label">{CATEGORY_LABELS[cat]}</span>
              <button
                type="button"
                onClick={() => toggleCollapsed(cat)}
                className={`prefs-toggle ${collapsed.includes(cat) ? "prefs-toggle--on" : ""}`}
              >
                {collapsed.includes(cat) ? "Sklopljeno" : "Sklopi na dno"}
              </button>
            </div>
            <input
              type="range"
              min={0}
              max={5}
              value={weights[cat]}
              onChange={(e) =>
                setWeights((w) => ({ ...w, [cat]: Number(e.target.value) }))
              }
              className="prefs-slider"
            />
            <div className="prefs-card__meta">
              <span>{WEIGHT_LABELS[weights[cat]]}</span>
              <span className="prefs-card__dots" aria-hidden>
                {"●".repeat(weights[cat])}
                <span className="prefs-card__dots-empty">{"○".repeat(5 - weights[cat])}</span>
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="prefs-actions">
        <button type="button" onClick={save} disabled={saving} className="auth-submit">
          {saving ? "Spremam…" : "Spremi postavke"}
        </button>
        {saved && <span className="prefs-saved">✓ Spremljeno — osvježi početnu za novi raspored</span>}
      </div>
    </div>
  );
}
