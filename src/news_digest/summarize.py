"""Ask Claude for a structured digest of the collected items."""
from __future__ import annotations

from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from .collect import Item

MODEL = "claude-opus-5-5"

SYSTEM = """You write a short daily news digest for busy founders and developers.
Rules:
- Use only facts present in the provided items. Never add numbers, names or claims that are not there.
- Group related items into one story when they cover the same event, and list every source URL.
- Skip items that are ads, job posts or not news.
- Write plainly: one-sentence summary, one sentence on why it matters for a small tech business."""


class Story(BaseModel):
    headline: str = Field(description="Short, neutral headline (max ~12 words)")
    summary: str = Field(description="One sentence: what happened")
    why_it_matters: str = Field(description="One sentence: impact for a small tech business")
    category: Literal["AI", "Developer tools", "Business", "Security", "Other"]
    importance: int = Field(ge=1, le=5, description="5 = must read")
    sources: list[str] = Field(description="URLs of the items this story is based on")


class Digest(BaseModel):
    intro: str = Field(description="One or two sentences on the day's theme")
    stories: list[Story]


class DigestRefused(RuntimeError):
    pass


def _items_block(items: list[Item]) -> str:
    return "\n\n".join(
        f"[{i}] {it.title}\nsource: {it.source}\nurl: {it.url}\n{it.summary}" for i, it in enumerate(items, 1)
    )


def summarize(items: list[Item], max_stories: int = 8, language: str = "English",
              client: anthropic.Anthropic | None = None) -> Digest:
    client = client or anthropic.Anthropic()  # ANTHROPIC_API_KEY or `ant auth login` profile
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=16000,
        # If the model declines, the API retries on Anthropic's recommended fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "medium"},
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Write the digest in {language} with at most {max_stories} stories, "
                       f"most important first.\n\n<items>\n{_items_block(items)}\n</items>",
        }],
        output_format=Digest,
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise DigestRefused(f"No digest returned (stop_reason={response.stop_reason})")
    digest: Digest = response.parsed_output
    digest.stories.sort(key=lambda s: -s.importance)
    return digest


def to_markdown(digest: Digest, title: str) -> str:
    lines = [f"# {title}", "", digest.intro, ""]
    for s in digest.stories:
        stars = "★" * s.importance + "☆" * (5 - s.importance)
        links = " · ".join(f"[source {n}]({u})" for n, u in enumerate(s.sources, 1))
        lines += [f"## {s.headline}", f"*{s.category} · {stars}*", "", s.summary, "",
                  f"**Why it matters:** {s.why_it_matters}", "", links, ""]
    return "\n".join(lines)
