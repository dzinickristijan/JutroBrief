"use client";

import Link from "next/link";
import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { dateHr } from "@/lib/personalize";

interface FavoriteItem {
  storyId: string;
  title: string;
  slug: string;
  issueDate: string;
}

export function FavoritesList({ items }: { items: FavoriteItem[] }) {
  const [list, setList] = useState(items);

  async function remove(storyId: string) {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;
    await supabase.from("favorites").delete().eq("user_id", user.id).eq("story_id", storyId);
    setList((prev) => prev.filter((f) => f.storyId !== storyId));
  }

  if (!list.length) {
    return (
      <p className="profile-empty">
        Nema spremljenih priča. Na stranici priče klikni &quot;Spremi u favorite&quot;.
      </p>
    );
  }

  return (
    <ul className="profile-list">
      {list.map((f) => (
        <li key={f.storyId} className="profile-list__item">
          <div className="profile-list__main">
            <Link href={`/prica/${f.issueDate}/${f.slug}`} className="profile-list__link">
              {f.title}
            </Link>
            <span className="profile-list__meta">{dateHr(f.issueDate)}</span>
          </div>
          <button
            type="button"
            onClick={() => remove(f.storyId)}
            className="profile-list__action"
            title="Ukloni iz favorita"
          >
            ✕
          </button>
        </li>
      ))}
    </ul>
  );
}
