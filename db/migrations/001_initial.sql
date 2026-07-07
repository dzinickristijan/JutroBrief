-- Jutarnji brief — Supabase schema (Auth-integrated)

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE story_category AS ENUM ('hr', 'svijet', 'biznis', 'sport', 'za_kraj');

-- ------------------------------------------------------------------ izdanja
CREATE TABLE editions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_date      DATE UNIQUE NOT NULL,
    title           TEXT NOT NULL,
    intro           TEXT,
    closing         TEXT,
    reading_minutes INT,
    published_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE stories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    edition_id      UUID NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    category        story_category NOT NULL,
    section_label   TEXT NOT NULL DEFAULT '',
    title           TEXT NOT NULL,
    slug            TEXT NOT NULL,
    summary         TEXT NOT NULL,
    source_url      TEXT NOT NULL,
    sort_order      INT NOT NULL,
    extended_body   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (edition_id, sort_order),
    UNIQUE (edition_id, slug)
);

CREATE INDEX idx_stories_edition ON stories(edition_id);
CREATE INDEX idx_stories_category ON stories(category);
CREATE INDEX idx_editions_date ON editions(issue_date DESC);

ALTER TABLE stories ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, ''))
    ) STORED;
CREATE INDEX idx_stories_search ON stories USING GIN(search_vector);

-- ------------------------------------------------------------------ korisnici (Supabase Auth)
CREATE TABLE profiles (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email           TEXT UNIQUE NOT NULL,
    display_name    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_preferences (
    user_id               UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    category_weights      JSONB NOT NULL DEFAULT '{
        "hr": 3, "svijet": 2, "biznis": 2, "sport": 1, "za_kraj": 1
    }'::jsonb,
    collapsed_categories  TEXT[] NOT NULL DEFAULT '{sport}',
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE favorites (
    user_id     UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    story_id    UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, story_id)
);

CREATE TABLE reading_history (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    edition_id    UUID NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    story_id      UUID REFERENCES stories(id) ON DELETE SET NULL,
    read_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    progress_pct  SMALLINT NOT NULL DEFAULT 100 CHECK (progress_pct BETWEEN 0 AND 100)
);

CREATE INDEX idx_history_user_date ON reading_history(user_id, read_at DESC);
CREATE INDEX idx_favorites_user ON favorites(user_id);

-- ------------------------------------------------------------------ auto-profil pri registraciji
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1))
    );
    INSERT INTO public.user_preferences (user_id) VALUES (NEW.id);
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ------------------------------------------------------------------ RLS
ALTER TABLE editions ENABLE ROW LEVEL SECURITY;
ALTER TABLE stories ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE reading_history ENABLE ROW LEVEL SECURITY;

-- Javno čitanje objavljenih izdanja
CREATE POLICY editions_public_read ON editions
    FOR SELECT USING (published_at IS NOT NULL);

CREATE POLICY stories_public_read ON stories
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM editions e
            WHERE e.id = stories.edition_id AND e.published_at IS NOT NULL
        )
    );

-- Profil — samo vlastiti
CREATE POLICY profiles_own_read ON profiles
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY profiles_own_update ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- Postavke — samo vlastite
CREATE POLICY prefs_own_read ON user_preferences
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY prefs_own_update ON user_preferences
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY prefs_own_insert ON user_preferences
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Favoriti
CREATE POLICY favorites_own_all ON favorites
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Povijest čitanja
CREATE POLICY history_own_read ON reading_history
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY history_own_insert ON reading_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY history_own_update ON reading_history
    FOR UPDATE USING (auth.uid() = user_id);

-- Service role (pipeline) upisuje izdanja — koristi service_role key u push_supabase.py
