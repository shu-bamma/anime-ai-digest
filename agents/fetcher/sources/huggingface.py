"""
Source fetcher: huggingface — papers + trending models RSS feeds.

See docs/SOURCE_EXPLORATION.md §1b for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)

FEEDS = [
    ("https://papers.takara.ai/api/feed", "hf_papers", "HuggingFace Papers"),
    ("https://zernel.github.io/huggingface-trending-feed/feed.xml", "hf_trending", "HuggingFace Trending"),
]

HF_KEYWORDS = ["video", "diffusion", "anime", "generation", "motion", "temporal",
               "wan", "i2v", "t2v", "lora", "animation"]


def _matches_keywords(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in HF_KEYWORDS)


def fetch() -> list[dict]:
    """Fetch from HuggingFace RSS feeds, filtered by keywords."""
    items = []
    for feed_url, source_id, feed_name in FEEDS:
        try:
            resp = requests.get(feed_url, timeout=config.REQUEST_TIMEOUT, headers={
                "User-Agent": config.USER_AGENT,
            })
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            count = 0
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                if not _matches_keywords(f"{title} {summary}"):
                    continue
                items.append({
                    "source_id": source_id,
                    "source_category": "models",
                    "title": title,
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", entry.get("updated", now_utc_iso())),
                    "raw_body": summary,
                    "original_language": "en",
                    "metadata": {},
                })
                count += 1
            logger.info(f"Fetched {count} items from {feed_name}")
        except Exception as e:
            logger.error(f"Failed to fetch {feed_name}: {e}")
    return items
