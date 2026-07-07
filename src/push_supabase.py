"""Push posts/*.md izdanja u Supabase.

Potrebno u .env:
  SUPABASE_URL=https://evygctviysfjwkatmfhx.supabase.co
  SUPABASE_SERVICE_ROLE_KEY=...  (Settings -> API -> service_role)

Upotreba:
  python src/push_supabase.py
  python src/push_supabase.py 2026-07-07
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ingest import ingest_file, issue_to_records  # noqa: E402


def load_env() -> None:
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text[:80] or "prica"


def clean_summary(summary: str) -> str:
    return re.sub(r"\s*\[Izvor\]\([^)]+\)\s*", "", summary).strip()


def reading_minutes(stories: list[dict]) -> int:
    words = sum(len(re.findall(r"\w+", s["summary"], flags=re.UNICODE)) for s in stories)
    return max(1, round(words / 200))


def main() -> None:
    load_env()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("GREŠKA: postavi SUPABASE_URL i SUPABASE_SERVICE_ROLE_KEY u .env")
        print("  Supabase -> Project Settings -> API -> service_role (secret)")
        sys.exit(1)

    try:
        from supabase import create_client
    except ImportError:
        print("Instaliraj: pip install supabase")
        sys.exit(1)

    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    client = create_client(url, key)

    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if date_arg:
        files = [f"posts/{date_arg}.md"]
    else:
        files = sorted(
            os.path.join("posts", f)
            for f in os.listdir("posts")
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", f)
        )

    if not files:
        print("Nema izdanja u posts/")
        return

    for path in files:
        if not os.path.exists(path):
            print(f"  [skip] {path} ne postoji")
            continue

        data = ingest_file(path)
        edition = data["edition"]
        stories = data["stories"]
        issue_date = edition["issue_date"]
        minutes = reading_minutes(stories)

        # intro cleanup — uzmi samo tekst nakon subject bloka
        intro = edition["intro"]
        if "Dobro jutro" in intro:
            intro = intro[intro.index("Dobro jutro") :]

        existing = (
            client.table("editions")
            .select("id")
            .eq("issue_date", issue_date)
            .maybe_single()
            .execute()
        )
        if existing and existing.data:
            edition_id = existing.data["id"]
            client.table("stories").delete().eq("edition_id", edition_id).execute()
            client.table("editions").update(
                {
                    "title": edition["title"],
                    "intro": intro,
                    "closing": edition.get("closing") or "",
                    "reading_minutes": minutes,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("id", edition_id).execute()
            print(f"  [update] {issue_date}")
        else:
            res = (
                client.table("editions")
                .insert(
                    {
                        "issue_date": issue_date,
                        "title": edition["title"],
                        "intro": intro,
                        "closing": edition.get("closing") or "",
                        "reading_minutes": minutes,
                        "published_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )
            edition_id = res.data[0]["id"]
            print(f"  [insert] {issue_date}")

        rows = []
        used_slugs: set[str] = set()
        for s in stories:
            base = slugify(s["title"])
            slug = base
            n = 2
            while slug in used_slugs:
                slug = f"{base}-{n}"
                n += 1
            used_slugs.add(slug)
            summary = clean_summary(s["summary"])
            if s["category"] == "za_kraj" and "To je to za jutros" in summary:
                parts = summary.split("To je to za jutros", 1)
                summary = parts[0].strip()
            rows.append(
                {
                    "edition_id": edition_id,
                    "category": s["category"],
                    "section_label": s.get("section_label", ""),
                    "title": s["title"],
                    "slug": slug,
                    "summary": summary,
                    "source_url": s["source_url"],
                    "sort_order": s["sort_order"],
                }
            )

        client.table("stories").insert(rows).execute()
        print(f"           {len(rows)} priča")

    print("\nSupabase sinkroniziran.")


if __name__ == "__main__":
    main()
