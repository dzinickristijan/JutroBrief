"""Generate seed SQL for Supabase execute_sql (one-time helper)."""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text[:80] or "prica"


def clean_summary(summary: str) -> str:
    s = re.sub(r"\s*\[Izvor\]\([^)]+\)\s*", "", summary).strip()
    if "To je to za jutros" in s:
        s = s.split("To je to za jutros", 1)[0].strip()
    return s


def sql_str(value: str) -> str:
    return "E'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main() -> None:
    data = json.loads((ROOT / "db/seed/2026-07-07.json").read_text(encoding="utf-8"))
    intro = data["edition"]["intro"]
    if "Dobro jutro" in intro:
        intro = intro[intro.index("Dobro jutro") :]

    words = sum(len(re.findall(r"\w+", s["summary"])) for s in data["stories"])
    minutes = max(1, round(words / 200))

    lines = [
        "DO $$",
        "DECLARE eid uuid;",
        "BEGIN",
        "DELETE FROM stories WHERE edition_id IN (SELECT id FROM editions WHERE issue_date = '2026-07-07');",
        "DELETE FROM editions WHERE issue_date = '2026-07-07';",
        f"INSERT INTO editions (issue_date, title, intro, closing, reading_minutes, published_at)",
        f"VALUES ('2026-07-07', {sql_str(data['edition']['title'])}, {sql_str(intro)}, '', {minutes}, now())",
        "RETURNING id INTO eid;",
    ]

    used: set[str] = set()
    for s in data["stories"]:
        base = slugify(s["title"])
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        summary = clean_summary(s["summary"])
        lines.append(
            "INSERT INTO stories (edition_id, category, section_label, title, slug, summary, source_url, sort_order) "
            f"VALUES (eid, '{s['category']}'::story_category, {sql_str(s.get('section_label', ''))}, "
            f"{sql_str(s['title'])}, {sql_str(slug)}, {sql_str(summary)}, {sql_str(s['source_url'])}, {s['sort_order']});"
        )

    lines.append("END $$;")
    out = ROOT / "db/seed" / "seed_2026-07-07.sql"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
