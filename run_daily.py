"""Jutarnji brief — dnevni pipeline.

Upotreba:
  python run_daily.py                # puni dnevni run: fetch -> draft -> save -> deliver
  python run_daily.py --check-feeds  # dijagnostika RSS izvora
  python run_daily.py --dry-run      # fetch + draft, bez slanja (draft ide u drafts/)
  python run_daily.py --quick        # skraćeno izdanje (degraded mode za bolesne dane)
  python run_daily.py --manual       # bez API-ja: pripremi prompt za paste u claude.ai/ChatGPT
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from fetch_news import load_config, fetch_all, check_feeds  # noqa: E402
from draft import draft_issue, write_manual_prompt  # noqa: E402
from deliver import send_email, notify_telegram  # noqa: E402


def main() -> None:
    args = set(sys.argv[1:])
    config = load_config()

    if "--check-feeds" in args:
        check_feeds(config)
        return

    if "--quick" in args:
        # Degraded mode: shorter window, model instructed via env flag if desired
        config["fetch_window_hours"] = min(config.get("fetch_window_hours", 20), 12)
        print("(quick mode — skraćeno izdanje)")

    print("1/4 Dohvaćam vijesti...")
    items = fetch_all(config)
    print(f"    Ukupno nakon deduplikacije: {len(items)}")
    if len(items) < 10:
        print("UPOZORENJE: premalo vijesti — provjeri feedove (--check-feeds).")
        if not items:
            sys.exit(1)

    if "--manual" in args:
        path = write_manual_prompt(items)
        print(f"2/2 Prompt spreman: {path}")
        print("    Otvori file, kopiraj SVE i zalijepi u claude.ai ili ChatGPT.")
        print("    Odgovor modela = tvoj draft. Uredi i pošalji kao i inače.")
        return

    print("2/4 Pišem draft (LLM)...")
    draft = draft_issue(items)

    print("3/4 Spremam draft...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("drafts", exist_ok=True)
    path = f"drafts/{date_str}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(draft)
    print(f"    {path}")

    if "--dry-run" in args:
        print("4/4 (dry-run — bez slanja)")
        return

    print("4/4 Dostavljam draft uredniku...")
    subject = f"[DRAFT] Jutarnji brief — {datetime.now().strftime('%d.%m.%Y.')}"
    send_email(subject, draft)
    notify_telegram(f"☕ Draft za {date_str} je spreman u tvom inboxu.")


if __name__ == "__main__":
    main()
