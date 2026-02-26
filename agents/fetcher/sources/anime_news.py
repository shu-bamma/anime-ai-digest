"""
Source fetcher: anime_news — Anime News Network RSS.

See docs/SOURCE_EXPLORATION.md §2a for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)

FEED_URL = "https://www.animenewsnetwork.com/all/rss.xml?ann-hierarchical"


def _matches_keywords(text: str) -> bool:
    return config.keyword_in_text(config.NEWS_KEYWORDS, text) > 0


def fetch() -> list[dict]:
    """Fetch ANN news filtered by AI/technology keywords."""
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
                "source_id": "ann_news",
                "source_category": "industry",
                "title": title,
                "url": entry.get("link", ""),
                "published_at": entry.get("published", now_utc_iso()),
                "raw_body": summary,
                "original_language": "en",
                "metadata": {},
            })
        logger.info(f"Fetched {len(items)} relevant items from ANN")
    except Exception as e:
        logger.error(f"Failed to fetch ANN: {e}")
    return items
