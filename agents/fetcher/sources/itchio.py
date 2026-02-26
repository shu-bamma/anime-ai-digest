"""
Source fetcher: itchio — itch.io interactive fiction RSS.

See docs/SOURCE_EXPLORATION.md §3h for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)

FEED_URL = "https://itch.io/games/tag-interactive-fiction/tag-twine.xml"


def fetch() -> list[dict]:
    """Fetch interactive fiction games from itch.io RSS."""
    items = []
    try:
        resp = requests.get(FEED_URL, timeout=config.REQUEST_TIMEOUT, headers={
            "User-Agent": config.USER_AGENT,
        })
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        for entry in feed.entries:
            items.append({
                "source_id": "itchio_if",
                "source_category": "community",
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "published_at": entry.get("published", now_utc_iso()),
                "raw_body": entry.get("summary", ""),
                "original_language": "en",
                "metadata": {},
            })
        logger.info(f"Fetched {len(items)} items from itch.io")
    except Exception as e:
        logger.error(f"Failed to fetch itch.io: {e}")
    return items
