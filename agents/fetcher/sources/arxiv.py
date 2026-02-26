"""
Source fetcher: arxiv — cs.CV RSS with keyword filter.

See docs/SOURCE_EXPLORATION.md §1c for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)

FEED_URL = "https://rss.arxiv.org/rss/cs.CV"


def _matches_keywords(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in config.ARXIV_KEYWORDS)


def fetch() -> list[dict]:
    """Fetch ArXiv cs.CV papers filtered by video/anime keywords."""
    items = []
    try:
        resp = requests.get(FEED_URL, timeout=config.REQUEST_TIMEOUT, headers={
            "User-Agent": config.USER_AGENT,
        })
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if not _matches_keywords(f"{title} {summary}"):
                continue
            items.append({
                "source_id": "arxiv_cv",
                "source_category": "models",
                "title": title,
                "url": entry.get("link", ""),
                "published_at": entry.get("published", entry.get("updated", now_utc_iso())),
                "raw_body": summary,
                "original_language": "en",
                "metadata": {
                    "authors": ", ".join(a.get("name", "") for a in entry.get("authors", [])),
                },
            })
        logger.info(f"Fetched {len(items)} relevant papers from ArXiv cs.CV")
    except Exception as e:
        logger.error(f"Failed to fetch ArXiv: {e}")
    return items
