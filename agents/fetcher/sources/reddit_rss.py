"""
Source fetcher: reddit_rss — 5 subreddit RSS feeds.

See docs/SOURCE_EXPLORATION.md §3c for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)


def fetch() -> list[dict]:
    """Fetch latest posts from tracked subreddits via RSS."""
    items = []
    for subreddit in config.REDDIT_SUBREDDITS:
        try:
            feed_url = f"https://www.reddit.com/r/{subreddit}/new/.rss"
            resp = requests.get(feed_url, timeout=config.REQUEST_TIMEOUT, headers={
                "User-Agent": config.USER_AGENT,
            })
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            count = 0
            for entry in feed.entries[:10]:
                items.append({
                    "source_id": f"reddit_{subreddit.lower()}",
                    "source_category": "community",
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", entry.get("updated", now_utc_iso())),
                    "raw_body": entry.get("summary", ""),
                    "original_language": "en",
                    "metadata": {
                        "subreddit": subreddit,
                        "author": entry.get("author", ""),
                    },
                })
                count += 1
            logger.info(f"Fetched {count} posts from r/{subreddit}")
        except Exception as e:
            logger.error(f"Failed to fetch r/{subreddit}: {e}")
    return items
