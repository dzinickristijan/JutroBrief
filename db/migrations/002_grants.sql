-- Dozvole za Supabase API uloge (anon + authenticated)
GRANT SELECT ON editions TO anon, authenticated;
GRANT SELECT ON stories TO anon, authenticated;
GRANT SELECT, UPDATE ON profiles TO authenticated;
GRANT SELECT, INSERT, UPDATE ON user_preferences TO authenticated;
GRANT SELECT, INSERT, DELETE ON favorites TO authenticated;
GRANT SELECT, INSERT, UPDATE ON reading_history TO authenticated;
