# Claude News Digest

> RSS/Atom feeds → de-duplicated → a **Claude-written daily digest** (Markdown) with "why it matters" for each story, in English, Urdu or Roman Urdu.

![python](https://img.shields.io/badge/python-3.10%2B-3776AB) ![claude](https://img.shields.io/badge/Claude-API-D97757) ![license](https://img.shields.io/badge/license-MIT-green)

## How it works

```
feeds.yaml ─▶ fetch (feedparser) ─▶ keep last N hours ─▶ de-duplicate ─▶ Claude (structured output) ─▶ digest.md
                                                         (URL + fuzzy title)   Pydantic schema
```

- **Grounded:** the system prompt forbids adding facts that are not in the feed items; every story lists its source URLs.
- **Structured outputs:** Claude returns a validated `Digest` (Pydantic) via `client.beta.messages.parse`, so the Markdown is rendered by code, never parsed from free text.
- **Resilient:** a broken feed is skipped; refusals are detected; server-side fallbacks (`fallbacks="default"`) are enabled.
- **Cheap to test:** `--dry-run` fetches and de-duplicates without calling the API.

## Quick start

```bash
pip install git+https://github.com/SameerD2logix/claude-news-digest
export ANTHROPIC_API_KEY=...        # or: ant auth login
news-digest --feeds feeds.yaml --hours 24 --out digest.md
news-digest --language "Roman Urdu"  # digest in Roman Urdu
news-digest --dry-run                # just list what was collected
```

See [`examples/digest-example.md`](examples/digest-example.md) for the output format.

## Automate it

Run daily with cron and send the file anywhere (email, Slack, WhatsApp via n8n):
```cron
0 9 * * *  cd /path/to/digest && news-digest --out "digest-$(date +\%F).md"
```

## Project layout

```
src/news_digest/collect.py     fetch + filter + de-duplicate
src/news_digest/summarize.py   Claude call, Pydantic schema, Markdown renderer
src/news_digest/cli.py         command line
tests/                         offline tests (fake client + sample feed)
```

## Tests

```bash
pip install -e . pytest && pytest -q
```
Tests are offline: the Claude call is replaced by a fake client.

## Author

**Sameer Hussain** · [LinkedIn](https://www.linkedin.com/in/sameer-hussain-87368a164) · [D2Logix](https://d2logix.com). The same idea powers an automated news-to-social-media pipeline.
