"""Generira SQL za ažuriranje punih sažetaka iz posts/*.md"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ingest import ingest_file  # noqa: E402


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text[:80] or "prica"


def sql_str(value: str) -> str:
    return "E'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def clean_summary(body: str) -> str:
    s = re.sub(r"\s*\[Izvor\]\([^)]+\)\s*", "", body).strip()
    if "To je to za jutros" in s:
        s = s.split("To je to za jutros", 1)[0].strip()
    return s


def main() -> None:
    posts = sorted(ROOT.glob("posts/*.md"))
    lines = ["BEGIN;"]
    for path in posts:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", path.stem):
            continue
        data = ingest_file(str(path))
        intro = data["edition"]["intro"]
        if "Dobro jutro" in intro:
            intro = intro[intro.index("Dobro jutro") :]
        closing = data["edition"].get("closing") or ""
        words = sum(len(re.findall(r"\w+", clean_summary(s["summary"]))) for s in data["stories"])
        minutes = max(1, round(words / 200))

        lines.append(
            f"UPDATE editions SET intro = {sql_str(intro)}, closing = {sql_str(closing)}, "
            f"reading_minutes = {minutes} WHERE issue_date = '{path.stem}';"
        )

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
                f"UPDATE stories SET summary = {sql_str(summary)} "
                f"WHERE slug = {sql_str(slug)} AND edition_id = (SELECT id FROM editions WHERE issue_date = '{path.stem}');"
            )

    lines.append("COMMIT;")
    out = ROOT / "db" / "seed" / "update_summaries.sql"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} ({len(lines)} statements)")


if __name__ == "__main__":
    main()
