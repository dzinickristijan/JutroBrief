"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

interface Props {
  storyId: string;
}

export function FavoriteButton({ storyId }: Props) {
  const [active, setActive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    async function load() {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        setLoggedIn(false);
        setLoading(false);
        return;
      }
      setLoggedIn(true);
      const { data } = await supabase
        .from("favorites")
        .select("story_id")
        .eq("user_id", user.id)
        .eq("story_id", storyId)
        .maybeSingle();
      setActive(!!data);
      setLoading(false);
    }
    load();
  }, [storyId]);

  async function toggle() {
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    if (active) {
      await supabase.from("favorites").delete().eq("user_id", user.id).eq("story_id", storyId);
      setActive(false);
    } else {
      await supabase.from("favorites").insert({ user_id: user.id, story_id: storyId });
      setActive(true);
    }
  }

  if (loading) return null;
  if (!loggedIn) {
    return (
      <a href="/prijava" className="favorite-btn favorite-btn--ghost">
        ♡ Prijavi se za favorite
      </a>
    );
  }

  return (
    <button
      type="button"
      onClick={toggle}
      className={`favorite-btn ${active ? "favorite-btn--active" : ""}`}
    >
      {active ? "★ U favoritima" : "☆ Spremi u favorite"}
    </button>
  );
}
