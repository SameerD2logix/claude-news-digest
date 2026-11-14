"""Command line: news-digest --feeds feeds.yaml [--hours 24] [--out digest.md] [--dry-run]"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

import yaml

from .collect import dedupe, fetch


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="news-digest", description="RSS feeds → Claude-written daily digest (Markdown)")
    ap.add_argument("--feeds", default="feeds.yaml", help="YAML file with a 'feeds' list of {name, url}")
    ap.add_argument("--hours", type=int, default=24, help="only items newer than this")
    ap.add_argument("--max-stories", type=int, default=8)
    ap.add_argument("--language", default="English", help='e.g. "English", "Urdu", "Roman Urdu"')
    ap.add_argument("--out", default="-", help="output Markdown file (default: stdout)")
    ap.add_argument("--dry-run", action="store_true", help="only list collected items, no API call")
    args = ap.parse_args(argv)

    with open(args.feeds, encoding="utf-8") as fh:
        feeds = yaml.safe_load(fh)["feeds"]

    items = dedupe(fetch(feeds, hours=args.hours))
    print(f"{len(items)} unique items from {len(feeds)} feeds", file=sys.stderr)
    if not items:
        print("Nothing new. No digest written.", file=sys.stderr)
        return 0
    if args.dry_run:
        for it in items:
            print(f"- [{it.source}] {it.title}\n  {it.url}")
        return 0

    from .summarize import summarize, to_markdown  # imported here so --dry-run needs no API key

    digest = summarize(items[:60], max_stories=args.max_stories, language=args.language)
    md = to_markdown(digest, f"News digest · {dt.date.today():%d %b %Y}")
    if args.out == "-":
        sys.stdout.write(md)
    else:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(md)
        print(f"Wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
