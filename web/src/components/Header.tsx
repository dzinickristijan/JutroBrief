import { createClient } from "@/lib/supabase/server";
import { HeaderNav } from "./HeaderNav";

export async function Header() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  return <HeaderNav userEmail={user?.email ?? null} />;
}
