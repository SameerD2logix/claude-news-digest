"""Fetch RSS/Atom feeds, keep recent items, and drop near-duplicate stories."""
from __future__ import annotations

import calendar
import re
import time
from dataclasses import dataclass
from difflib import SequenceMatcher

import feedparser

USER_AGENT = "claude-news-digest/0.1 (+https://github.com/SameerD2logix/claude-news-digest)"
TAGS = re.compile(r"<[^>]+>")


@dataclass
class Item:
    title: str
    url: str
    source: str
    published: float  # unix seconds
    summary: str = ""


def _clean(text: str, limit: int = 600) -> str:
    text = " ".join(TAGS.sub(" ", text or "").split())
    return text[:limit] + ("…" if len(text) > limit else "")


def fetch(feeds: list[dict], hours: int = 24, per_feed: int = 15, now: float | None = None) -> list[Item]:
    """Read every feed; keep items newer than `hours`. A broken feed is skipped, not fatal."""
    cutoff = (now or time.time()) - hours * 3600
    items: list[Item] = []
    for feed in feeds:
        parsed = feedparser.parse(feed["url"], agent=USER_AGENT)
        for entry in parsed.entries[:per_feed]:
            stamp = entry.get("published_parsed") or entry.get("updated_parsed")
            published = calendar.timegm(stamp) if stamp else 0.0
            if published and published < cutoff:
                continue
            items.append(Item(
                title=_clean(entry.get("title", ""), 200),
                url=entry.get("link", ""),
                source=feed.get("name") or parsed.feed.get("title", feed["url"]),
                published=published,
                summary=_clean(entry.get("summary", "")),
            ))
    return items


def _key(title: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", title.lower()).split())


def dedupe(items: list[Item], threshold: float = 0.85) -> list[Item]:
    """Drop items whose URL repeats or whose title is ~the same story (keeps the earliest seen)."""
    kept: list[Item] = []
    seen_urls: set[str] = set()
    for it in sorted(items, key=lambda i: -i.published):
        if it.url and it.url in seen_urls:
            continue
        k = _key(it.title)
        if any(SequenceMatcher(None, k, _key(o.title)).ratio() >= threshold for o in kept):
            continue
        kept.append(it)
        seen_urls.add(it.url)
    return kept
