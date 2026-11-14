from pathlib import Path
from types import SimpleNamespace

import pytest

from news_digest.collect import Item, dedupe, fetch
from news_digest.summarize import Digest, DigestRefused, Story, summarize, to_markdown

FEED = Path(__file__).parent / "sample_feed.xml"


def test_fetch_reads_local_feed_and_filters_by_age():
    now = 1_763_000_000  # fixed clock
    items = fetch([{"name": "Sample", "url": str(FEED)}], hours=48, now=now)
    titles = [i.title for i in items]
    assert "New open model released" in titles
    assert "Very old story" not in titles
    assert all(i.source == "Sample" for i in items)
    assert "<b>" not in items[0].summary


def test_dedupe_by_url_and_similar_title():
    items = [
        Item("Claude gets new feature", "https://a/1", "A", 3),
        Item("Claude gets new feature!", "https://b/2", "B", 2),
        Item("Something else entirely", "https://a/1", "C", 1),
        Item("Different story", "https://c/3", "C", 0),
    ]
    assert [i.url for i in dedupe(items)] == ["https://a/1", "https://c/3"]


class FakeClient:
    def __init__(self, parsed, stop_reason="end_turn"):
        self.calls = []
        msgs = SimpleNamespace(parse=self._parse)
        self.beta = SimpleNamespace(messages=msgs)
        self._parsed, self._stop = parsed, stop_reason

    def _parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(parsed_output=self._parsed, stop_reason=self._stop)


def story(h, imp):
    return Story(headline=h, summary="s", why_it_matters="w", category="AI", importance=imp, sources=["https://x"])


def test_summarize_sends_items_and_sorts_by_importance():
    fake = FakeClient(Digest(intro="Today", stories=[story("low", 2), story("high", 5)]))
    d = summarize([Item("T1", "https://x", "S", 1, "body")], client=fake)
    assert [s.headline for s in d.stories] == ["high", "low"]
    call = fake.calls[0]
    assert call["model"] == "claude-opus-5-5" and call["output_format"] is Digest
    assert call["fallbacks"] == "default" and "T1" in call["messages"][0]["content"]


def test_refusal_raises():
    with pytest.raises(DigestRefused):
        summarize([Item("T", "u", "S", 1)], client=FakeClient(None, "refusal"))


def test_markdown():
    md = to_markdown(Digest(intro="Hi", stories=[story("Big news", 4)]), "Digest")
    assert "## Big news" in md and "★★★★☆" in md and "[source 1](https://x)" in md
