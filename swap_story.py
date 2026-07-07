"""Zamijeni priču u izdanju stavkom s B-liste.

Upotreba:
  python swap_story.py --list                    # prikaži numeraciju
  python swap_story.py --out 5 --in 3            # zamijeni 5. priču s 3. s B-liste
  python swap_story.py --date 2026-07-07 --out 2 --in 1
"""

import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from issue_parser import list_stories, parse_issue, serialize_issue, swap_story  # noqa: E402


def resolve_path(date_str: str, drafts: bool) -> str:
    folder = "drafts" if drafts else "posts"
    path = os.path.join(folder, f"{date_str}.md")
    if not os.path.exists(path):
        alt = "posts" if drafts else "drafts"
        alt_path = os.path.join(alt, f"{date_str}.md")
        if os.path.exists(alt_path):
            return alt_path
        raise FileNotFoundError(f"Nema izdanja: {path}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Zamjena priče s B-liste u draftu/izdanju.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--drafts", action="store_true", help="Uredi drafts/ umjesto posts/")
    parser.add_argument("--list", action="store_true", help="Prikaži priče i B-listu")
    parser.add_argument("--out", type=int, help="Broj priče za zamjenu (1-based)")
    parser.add_argument("--in", dest="in_idx", type=int, help="Broj stavke s B-liste (1-based)")
    args = parser.parse_args()

    path = resolve_path(args.date, args.drafts)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    doc = parse_issue(text)

    if args.list:
        print(list_stories(doc))
        return

    if args.out is None or args.in_idx is None:
        parser.error("Za zamjenu navedi --out N --in M (ili samo --list).")

    doc = swap_story(doc, args.out, args.in_idx)
    new_text = serialize_issue(doc)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_text)

    out_story = doc.stories[args.out - 1]
    print(f"Zamijenjeno u {path}:")
    print(f"  Priča #{args.out} sada: {out_story.title}")
    print("  Sažetak je placeholder — dopuni ga prije objave.")


if __name__ == "__main__":
    main()
