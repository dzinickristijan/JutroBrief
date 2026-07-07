"use client";

import { useEffect } from "react";
import { createClient } from "@/lib/supabase/client";

interface Props {
  editionId: string;
  storyId: string;
}

export function RecordRead({ editionId, storyId }: Props) {
  useEffect(() => {
    async function record() {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data: existing } = await supabase
        .from("reading_history")
        .select("id")
        .eq("user_id", user.id)
        .eq("story_id", storyId)
        .maybeSingle();

      if (existing) {
        await supabase
          .from("reading_history")
          .update({ read_at: new Date().toISOString(), progress_pct: 100 })
          .eq("id", existing.id);
      } else {
        await supabase.from("reading_history").insert({
          user_id: user.id,
          edition_id: editionId,
          story_id: storyId,
          progress_pct: 100,
        });
      }
    }
    record();
  }, [editionId, storyId]);

  return null;
}
