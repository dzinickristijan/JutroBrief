"""Objavi izdanje u jednom koraku: draft → posts → docs.

Upotreba:
  python publish_issue.py                  # današnji datum
  python publish_issue.py 2026-07-07       # određeni datum
  python publish_issue.py --from-posts     # preskoči kopiranje, samo generiraj docs/
"""

import argparse
import os
import shutil
import sys
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Kopira draft u posts/ i generira docs/.")
    parser.add_argument("date", nargs="?", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--from-posts", action="store_true", help="Ne kopiraj iz drafts/, samo publish.py")
    args = parser.parse_args()

    date_str = args.date
    draft_path = os.path.join("drafts", f"{date_str}.md")
    post_path = os.path.join("posts", f"{date_str}.md")

    if not args.from_posts:
        if not os.path.exists(draft_path):
            if os.path.exists(post_path):
                print(f"Draft {draft_path} ne postoji — koristim postojeći {post_path}")
            else:
                print(f"GREŠKA: nema {draft_path} ni {post_path}")
                sys.exit(1)
        else:
            shutil.copy2(draft_path, post_path)
            print(f"Kopirano: {draft_path} → {post_path}")

    from publish import main as publish_main

    publish_main()

    if "--supabase" in sys.argv:
        print("\nSinkronizacija s Supabase...")
        import subprocess
        subprocess.run([sys.executable, "src/push_supabase.py", date_str], check=False)

    print("\nSljedeći korak: push na GitHub (GitHub Desktop ili git push).")


if __name__ == "__main__":
    main()
