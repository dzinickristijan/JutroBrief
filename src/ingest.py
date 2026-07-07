"""Parsira posts/*.md u strukturirani JSON spreman za PostgreSQL ingest."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from issue_parser import IssueDocument, parse_issue  # noqa: E402

SECTION_TO_CATEGORY = {
    "hrvatska": "hr",
    "svijet": "svijet",
    "biznis": "biznis",
    "sport": "sport",
    "za kraj": "za_kraj",
}


def section_category(section: str) -> str:
    low = section.lower()
    for key, cat in SECTION_TO_CATEGORY.items():
        if key in low:
            return cat
    return "svijet"


def extract_source_url(body: str) -> str:
    m = re.search(r"\[Izvor\]\(([^)]+)\)", body)
    return m.group(1) if m else ""


def extract_intro(preamble: str) -> tuple[str, str]:
    lines = preamble.splitlines()
    title = ""
    intro_lines: list[str] = []
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.strip() and not line.startswith("##"):
            text = line.strip()
            # Preskoči subject line prijedloge iz drafta
            if re.match(r"^\d+\.\s", text):
                continue
            intro_lines.append(text)
    intro = " ".join(intro_lines)
    if "Dobro jutro" in intro:
        intro = intro[intro.index("Dobro jutro") :]
    return title, intro


def issue_to_records(doc: IssueDocument, issue_date: str) -> dict:
    title, intro = extract_intro(doc.preamble)
    edition = {
        "issue_date": issue_date,
        "title": title or f"Jutarnji brief — {issue_date}",
        "intro": intro,
        "closing": doc.closing,
    }
    stories = []
    for i, s in enumerate(doc.stories, start=1):
        stories.append(
            {
                "category": section_category(s.section),
                "title": s.title,
                "summary": s.body,
                "source_url": extract_source_url(s.body),
                "sort_order": i,
                "section_label": s.section,
            }
        )
    return {"edition": edition, "stories": stories}


def ingest_file(path: str) -> dict:
    slug = os.path.splitext(os.path.basename(path))[0]
    with open(path, "r", encoding="utf-8") as f:
        doc = parse_issue(f.read())
    return issue_to_records(doc, slug)


def main() -> None:
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    posts_dir = "posts"
    files = sorted(
        f for f in os.listdir(posts_dir)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", f)
    )
    if not files:
        print("Nema izdanja u posts/")
        return

    out_dir = os.path.join("db", "seed")
    os.makedirs(out_dir, exist_ok=True)

    for fname in files:
        path = os.path.join(posts_dir, fname)
        data = ingest_file(path)
        out_path = os.path.join(out_dir, fname.replace(".md", ".json"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  [OK] {fname} -> {out_path}")

    print(f"\n{len(files)} izdanja spremno za import u PostgreSQL.")


if __name__ == "__main__":
    main()
