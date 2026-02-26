"""
Source fetcher: pixiv — via RSSHub.

See docs/SOURCE_EXPLORATION.md §3e for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)

SEARCH_TERMS = ["AI動画", "AI生成", "AIイラスト"]


def fetch() -> list[dict]:
    """Fetch Pixiv AI art/video content via RSSHub search routes."""
    items = []
    rsshub = config.RSSHUB_URL.rstrip("/")

    for term in SEARCH_TERMS:
        try:
            feed_url = f"{rsshub}/pixiv/search/{term}/popular"
            resp = requests.get(feed_url, timeout=config.REQUEST_TIMEOUT, headers={
                "User-Agent": config.USER_AGENT,
            })
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            count = 0
            for entry in feed.entries[:10]:
                items.append({
                    "source_id": "pixiv_ai",
                    "source_category": "community",
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", now_utc_iso()),
                    "raw_body": entry.get("summary", ""),
                    "original_language": "ja",
                    "metadata": {"search_term": term},
                })
                count += 1
            logger.info(f"Fetched {count} items from Pixiv [{term}]")
        except Exception as e:
            logger.warning(f"Failed to fetch Pixiv [{term}]: {e}")

    # Deduplicate by URL
    seen = set()
    deduped = []
    for item in items:
        if item["url"] not in seen:
            seen.add(item["url"])
            deduped.append(item)
    return deduped
