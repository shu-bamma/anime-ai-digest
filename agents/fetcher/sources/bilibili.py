"""
Source fetcher: bilibili — via RSSHub.

See docs/SOURCE_EXPLORATION.md §2d for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)


def fetch() -> list[dict]:
    """Fetch Bilibili AI animation content via RSSHub search routes."""
    items = []
    rsshub = config.RSSHUB_URL.rstrip("/")

    for keyword in config.BILIBILI_KEYWORDS:
        try:
            feed_url = f"{rsshub}/bilibili/search/{keyword}"
            resp = requests.get(feed_url, timeout=config.REQUEST_TIMEOUT, headers={
                "User-Agent": config.USER_AGENT,
            })
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            count = 0
            for entry in feed.entries[:10]:
                items.append({
                    "source_id": "bilibili_ai",
                    "source_category": "community",
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", entry.get("updated", now_utc_iso())),
                    "raw_body": entry.get("summary", ""),
                    "original_language": "zh",
                    "metadata": {
                        "search_keyword": keyword,
                    },
                })
                count += 1
            logger.info(f"Fetched {count} items from Bilibili [{keyword}]")
        except Exception as e:
            logger.warning(f"Failed to fetch Bilibili [{keyword}]: {e}")

    # Deduplicate by URL
    seen = set()
    deduped = []
    for item in items:
        if item["url"] not in seen:
            seen.add(item["url"])
            deduped.append(item)
    logger.info(f"Bilibili total: {len(deduped)} unique items")
    return deduped
