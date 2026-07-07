"""Fetch and deduplicate news items from RSS feeds defined in config/sources.yaml."""

import re
import time
import html
from datetime import datetime, timedelta, timezone

import yaml
import feedparser


def load_config(path: str = "config/sources.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _clean_text(text: str, max_len: int = 400) -> str:
    """Strip HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _entry_time(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime.fromtimestamp(time.mktime(t), tz=timezone.utc)
    return None


def _normalize_title(title: str) -> str:
    """Normalized form used for near-duplicate detection."""
    t = title.lower()
    t = re.sub(r"[^a-z0-9čćžšđ ]", "", t)
    words = [w for w in t.split() if len(w) > 3]
    return " ".join(sorted(words)[:8])


def fetch_all(config: dict, verbose: bool = True) -> list[dict]:
    """Fetch entries from all feeds within the configured time window."""
    window = timedelta(hours=config.get("fetch_window_hours", 20))
    cutoff = datetime.now(timezone.utc) - window
    items: list[dict] = []
    seen_links: set[str] = set()
    seen_titles: set[str] = set()

    for source in config["sources"]:
        name, url = source["name"], source["url"]
        try:
            feed = feedparser.parse(url)
        except Exception as e:  # noqa: BLE001
            if verbose:
                print(f"  [FAIL] {name}: {e}")
            continue

        if feed.bozo and not feed.entries:
            if verbose:
                print(f"  [FAIL] {name}: neispravan feed ({url})")
            continue

        count = 0
        for entry in feed.entries:
            link = getattr(entry, "link", "") or ""
            title = _clean_text(getattr(entry, "title", ""), 200)
            if not link or not title:
                continue

            published = _entry_time(entry)
            # Keep undated entries (some feeds omit dates) but drop old ones.
            if published and published < cutoff:
                continue

            norm = _normalize_title(title)
            if link in seen_links or (norm and norm in seen_titles):
                continue
            seen_links.add(link)
            if norm:
                seen_titles.add(norm)

            items.append(
                {
                    "source": name,
                    "section_hint": source.get("section_hint", ""),
                    "title": title,
                    "summary": _clean_text(
                        getattr(entry, "summary", "") or getattr(entry, "description", "")
                    ),
                    "link": link,
                    "published": published.isoformat() if published else "",
                }
            )
            count += 1

        if verbose:
            print(f"  [OK]   {name}: {count} vijesti")

    items.sort(key=lambda x: x["published"], reverse=True)
    return items


def check_feeds(config: dict) -> None:
    """Diagnostic mode: report health of every configured feed."""
    print("Provjera feedova:\n")
    for source in config["sources"]:
        try:
            feed = feedparser.parse(source["url"])
            n = len(feed.entries)
            status = f"OK, {n} zapisa" if n else "PRAZAN ili neispravan"
        except Exception as e:  # noqa: BLE001
            status = f"GREŠKA: {e}"
        print(f"  {source['name']:<22} {status}")
    print("\nPrazne/neispravne feedove zamijeni u config/sources.yaml.")
