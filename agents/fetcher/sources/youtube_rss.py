"""
Source fetcher: youtube_rss — 7 channel RSS feeds.

See docs/SOURCE_EXPLORATION.md §4 for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)


def fetch() -> list[dict]:
    """Fetch latest videos from tracked YouTube channels via RSS."""
    items = []
    for channel_id, name, source_id in config.YOUTUBE_CHANNELS:
        try:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            resp = requests.get(feed_url, timeout=config.REQUEST_TIMEOUT, headers={
                "User-Agent": config.USER_AGENT,
            })
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            count = 0
            for entry in feed.entries[:5]:
                video_id = entry.get("yt_videoid", "")
                items.append({
                    "source_id": source_id,
                    "source_category": "youtube",
                    "title": entry.get("title", ""),
                    "url": entry.get("link", f"https://www.youtube.com/watch?v={video_id}"),
                    "published_at": entry.get("published", now_utc_iso()),
                    "raw_body": entry.get("summary", ""),
                    "original_language": "en",
                    "metadata": {
                        "channel": name,
                        "video_id": video_id,
                        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else "",
                    },
                })
                count += 1
            logger.info(f"Fetched {count} videos from {name}")
        except Exception as e:
            logger.error(f"Failed to fetch YouTube channel {name}: {e}")
    return items
