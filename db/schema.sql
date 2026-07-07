-- Jutarnji brief — PostgreSQL schema
-- Preporuka: Supabase (PostgreSQL + Auth) ili Neon + vlastiti auth sloj

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------ korisnici
-- Ako koristiš Supabase Auth, profiles.id = auth.users.id (UUID).

CREATE TABLE profiles (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE NOT NULL,
    display_name  TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_preferences (
    user_id       UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    -- Težine rubrika: veći broj = više naglaska i više priča iz te rubrike
    -- Ključevi: hr, svijet, biznis, sport, za_kraj
    category_weights JSONB NOT NULL DEFAULT '{
        "hr": 3,
        "svijet": 2,
        "biznis": 2,
        "sport": 1,
        "za_kraj": 1
    }'::jsonb,
    -- Rubrike s težinom 0 idu na dno u sklopivom bloku
    collapsed_categories TEXT[] NOT NULL DEFAULT '{sport}',
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ------------------------------------------------------------------ izdanja
CREATE TABLE editions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_date    DATE UNIQUE NOT NULL,
    title         TEXT NOT NULL,
    intro         TEXT,
    closing       TEXT,
    reading_minutes INT,
    published_at  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE story_category AS ENUM ('hr', 'svijet', 'biznis', 'sport', 'za_kraj');

CREATE TABLE stories (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    edition_id    UUID NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    category      story_category NOT NULL,
    title         TEXT NOT NULL,
    summary       TEXT NOT NULL,
    source_url    TEXT NOT NULL,
    sort_order    INT NOT NULL,
    -- Za proširenu priču (kasnije)
    extended_body TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (edition_id, sort_order)
);

CREATE INDEX idx_stories_edition ON stories(edition_id);
CREATE INDEX idx_stories_category ON stories(category);
CREATE INDEX idx_editions_date ON editions(issue_date DESC);

-- ------------------------------------------------------------------ čitatelj
CREATE TABLE favorites (
    user_id       UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    story_id      UUID NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
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

-- ------------------------------------------------------------------ pretraga (arhiva)
-- tsvector za full-text pretragu po naslovu i sažetku
ALTER TABLE stories ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, ''))
    ) STORED;

CREATE INDEX idx_stories_search ON stories USING GIN(search_vector);

-- ------------------------------------------------------------------ mapiranje emoji rubrika → enum
-- 🇭🇷 HRVATSKA → hr
-- 🌍 SVIJET → svijet
-- 💼 BIZNIS & TECH → biznis
-- ⚽ SPORT → sport
-- ☕ ZA KRAJ → za_kraj
