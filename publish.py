"""Generator web stranice: pretvara posts/*.md u statičku stranicu u docs/.

Upotreba:
  1. Uređeno izdanje spremi kao posts/GGGG-MM-DD.md  (npr. posts/2026-07-06.md)
  2. python publish.py
  3. git add . && git commit -m "izdanje" && git push
     (GitHub Pages servira docs/ — vidi README)

Generator automatski izbacuje urednička poglavlja (SUBJECT PRIJEDLOZI, B-LISTA).
"""

import os
import re
import glob
import html
from datetime import datetime, timezone

import yaml
import markdown

POSTS_DIR = "posts"
OUT_DIR = "docs"

MONTHS_HR = [
    "", "siječnja", "veljače", "ožujka", "travnja", "svibnja", "lipnja",
    "srpnja", "kolovoza", "rujna", "listopada", "studenoga", "prosinca",
]

EDITOR_SECTIONS = ("subject", "b-lista", "b lista")


# ------------------------------------------------------------------ helpers

def load_site_config() -> dict:
    with open("config/site.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg.setdefault("title", "Jutarnji brief")
    cfg.setdefault("tagline", "")
    cfg.setdefault("author", "")
    cfg.setdefault("base_url", "")
    cfg.setdefault("newsletter_url", "")
    return cfg


def date_hr(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{d.day}. {MONTHS_HR[d.month]} {d.year}."


def strip_editor_sections(md_text: str) -> str:
    """Remove h2 sections meant only for the editor (subject ideas, B-list)."""
    out, skipping = [], False
    for line in md_text.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            skipping = any(key in heading for key in EDITOR_SECTIONS)
            if skipping:
                continue
        if not skipping:
            out.append(line)
    return "\n".join(out).strip()


def reading_minutes(md_text: str) -> int:
    words = len(re.findall(r"\w+", md_text, flags=re.UNICODE))
    return max(1, round(words / 200))


def md_to_html(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["extra"])


# ------------------------------------------------------------------ template

STYLE_CSS = """
:root {
  --paper: #FAF7F1;
  --ink: #262019;
  --espresso: #3B2E23;
  --sun: #E8A11C;
  --muted: #756A5C;
  --line: #E4DCCF;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 17px;
  line-height: 1.65;
}
.wrap { max-width: 680px; margin: 0 auto; padding: 0 20px 64px; }

/* masthead */
header.mast { padding: 40px 0 20px; border-bottom: 3px solid var(--espresso); }
.mast a { text-decoration: none; color: inherit; }
.mast h1 {
  font-family: Fraunces, Georgia, serif;
  font-weight: 700;
  font-size: clamp(2rem, 6vw, 2.9rem);
  letter-spacing: -0.02em;
  margin: 0;
}
.mast h1 .dot { color: var(--sun); }
.mast .tagline { color: var(--muted); margin: 4px 0 0; font-size: 0.95rem; }

/* issue meta */
.issue-meta {
  display: flex; flex-wrap: wrap; gap: 12px; align-items: baseline;
  margin: 28px 0 6px;
}
.issue-date {
  font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.14em;
  color: var(--muted);
}
.badge {
  font-size: 0.8rem; font-weight: 600; color: var(--espresso);
  background: #F1E6CE; border-radius: 999px; padding: 2px 12px;
}

/* article body */
article h2 {
  font-family: Fraunces, Georgia, serif;
  font-size: 1.35rem;
  margin: 2.2em 0 0.6em;
  padding-bottom: 4px;
  border-bottom: 2px solid var(--sun);
}
article h1 { display: none; } /* naslov izdanja dolazi iz metapodataka */
article p { margin: 0.9em 0; }
article strong { color: var(--espresso); }
article a { color: var(--espresso); text-decoration-color: var(--sun); text-underline-offset: 3px; }
article a:hover { color: var(--sun); }
article hr { border: 0; border-top: 1px solid var(--line); margin: 2em 0; }

/* archive list */
.arhiva { margin-top: 48px; padding-top: 16px; border-top: 1px solid var(--line); }
.arhiva h2 {
  font-family: Fraunces, Georgia, serif; font-size: 1.1rem; color: var(--muted);
  text-transform: uppercase; letter-spacing: 0.1em; border: 0;
}
.arhiva ul { list-style: none; padding: 0; margin: 0; }
.arhiva li { padding: 8px 0; border-bottom: 1px dashed var(--line); }
.arhiva a { color: var(--ink); text-decoration: none; }
.arhiva a:hover { color: var(--espresso); text-decoration: underline; text-decoration-color: var(--sun); }
.arhiva .d { color: var(--muted); font-size: 0.85rem; margin-left: 8px; }

/* newsletter box */
.mail-box {
  margin-top: 40px; padding: 16px 20px; border: 1px solid var(--line);
  border-left: 4px solid var(--sun); border-radius: 4px; font-size: 0.95rem;
}
.mail-box a { color: var(--espresso); font-weight: 600; }

footer.foot {
  margin-top: 56px; padding-top: 16px; border-top: 3px solid var(--espresso);
  color: var(--muted); font-size: 0.85rem;
}
a:focus-visible { outline: 3px solid var(--sun); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""

PAGE_TMPL = """<!doctype html>
<html lang="hr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PAGE_TITLE__</title>
<meta name="description" content="__TAGLINE__">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
<link rel="alternate" type="application/rss+xml" title="__SITE_TITLE__" href="feed.xml">
</head>
<body>
<div class="wrap">
  <header class="mast">
    <a href="index.html"><h1>__SITE_TITLE__<span class="dot">.</span></h1></a>
    <p class="tagline">__TAGLINE__</p>
  </header>
  __CONTENT__
  __MAILBOX__
  <footer class="foot">__FOOTER__</footer>
</div>
</body>
</html>
"""


def render_page(cfg: dict, page_title: str, content: str) -> str:
    mailbox = ""
    if cfg["newsletter_url"]:
        mailbox = (
            '<div class="mail-box">Ne želiš provjeravati stranicu? '
            f'<a href="{html.escape(cfg["newsletter_url"])}">Primaj izdanja mailom</a>.</div>'
        )
    footer = f"© {datetime.now().year} {html.escape(cfg['author'] or cfg['title'])} · Sažeci pisani vlastitim riječima, uz linkove na izvore."
    return (
        PAGE_TMPL
        .replace("__PAGE_TITLE__", html.escape(page_title))
        .replace("__SITE_TITLE__", html.escape(cfg["title"]))
        .replace("__TAGLINE__", html.escape(cfg["tagline"]))
        .replace("__CONTENT__", content)
        .replace("__MAILBOX__", mailbox)
        .replace("__FOOTER__", footer)
    )


def issue_html(date_str: str, minutes: int, body_html: str) -> str:
    return (
        '<article>'
        f'<div class="issue-meta"><span class="issue-date">{date_hr(date_str)}</span>'
        f'<span class="badge">☕ {minutes} min čitanja</span></div>'
        f'{body_html}</article>'
    )


def build_rss(cfg: dict, posts: list[dict]) -> str:
    base = cfg["base_url"].rstrip("/")
    items = []
    for p in posts[:20]:
        link = f"{base}/{p['slug']}.html" if base else f"{p['slug']}.html"
        items.append(
            "<item>"
            f"<title>{html.escape(cfg['title'])} — {date_hr(p['date'])}</title>"
            f"<link>{html.escape(link)}</link>"
            f"<guid>{html.escape(link)}</guid>"
            f"<pubDate>{datetime.strptime(p['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc).strftime('%a, %d %b %Y 06:00:00 +0000')}</pubDate>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel>'
        f"<title>{html.escape(cfg['title'])}</title>"
        f"<link>{html.escape(base or '/')}</link>"
        f"<description>{html.escape(cfg['tagline'])}</description>"
        f"{''.join(items)}"
        "</channel></rss>"
    )


# ------------------------------------------------------------------ main

def main() -> None:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    cfg = load_site_config()

    files = sorted(glob.glob(os.path.join(POSTS_DIR, "*.md")), reverse=True)
    if not files:
        print(f"Nema izdanja u {POSTS_DIR}/ — spremi uređeni draft kao {POSTS_DIR}/GGGG-MM-DD.md pa ponovi.")
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    posts = []
    for path in files:
        slug = os.path.splitext(os.path.basename(path))[0]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", slug):
            print(f"  [skip] {path} — ime mora biti GGGG-MM-DD.md")
            continue
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        clean = strip_editor_sections(raw)
        minutes = reading_minutes(clean)
        body = issue_html(slug, minutes, md_to_html(clean))
        page = render_page(cfg, f"{cfg['title']} — {date_hr(slug)}", body)
        with open(os.path.join(OUT_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(page)
        posts.append({"slug": slug, "date": slug, "minutes": minutes, "body": body})
        print(f"  [OK] {slug} ({minutes} min)")

    # index: najnovije izdanje + arhiva
    latest = posts[0]
    archive_items = "".join(
        f'<li><a href="{p["slug"]}.html">Izdanje — {date_hr(p["date"])}</a>'
        f'<span class="d">☕ {p["minutes"]} min</span></li>'
        for p in posts[1:]
    )
    archive = f'<section class="arhiva"><h2>Arhiva</h2><ul>{archive_items}</ul></section>' if archive_items else ""
    index = render_page(cfg, cfg["title"], latest["body"] + archive)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index)

    with open(os.path.join(OUT_DIR, "style.css"), "w", encoding="utf-8") as f:
        f.write(STYLE_CSS)
    with open(os.path.join(OUT_DIR, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(build_rss(cfg, posts))
    # GitHub Pages: bez Jekyll obrade
    open(os.path.join(OUT_DIR, ".nojekyll"), "w").close()

    print(f"\nStranica generirana u {OUT_DIR}/ — {len(posts)} izdanja. Push na GitHub i online je.")


if __name__ == "__main__":
    main()
