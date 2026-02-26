"""
Source fetcher: gigazine — Japanese tech news RSS with keyword filter.

See docs/SOURCE_EXPLORATION.md §2c for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)

FEED_URL = "https://gigazine.net/news/rss_2.0/"


def _matches_keywords(text: str) -> bool:
    return config.keyword_in_text(config.JP_KEYWORDS, text) > 0


def fetch() -> list[dict]:
    """Fetch GIGAZINE articles filtered by AI/anime keywords."""
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
                "source_id": "gigazine",
                "source_category": "industry",
                "title": title,
                "url": entry.get("link", ""),
                "published_at": entry.get("published", now_utc_iso()),
                "raw_body": summary,
                "original_language": "ja",
                "metadata": {},
            })
        logger.info(f"Fetched {len(items)} relevant items from GIGAZINE")
    except Exception as e:
        logger.error(f"Failed to fetch GIGAZINE: {e}")
    return items
