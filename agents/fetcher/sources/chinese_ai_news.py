"""
Source fetcher: chinese_ai_news — 36kr & 机器之心 via RSSHub.

See docs/SOURCE_EXPLORATION.md §2e for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)

FEEDS = [
    ("/36kr/newsflashes", "36kr", "36kr News"),
    ("/jiqizhixin/daily", "jiqizhixin", "机器之心"),
]

AI_KEYWORDS = ["ai", "视频", "动画", "模型", "开源", "video", "anime",
               "diffusion", "wan", "生成", "lora"]


def _matches_keywords(text: str) -> bool:
    return config.keyword_in_text(AI_KEYWORDS, text) > 0


def fetch() -> list[dict]:
    """Fetch Chinese AI news from 36kr and 机器之心 via RSSHub."""
    items = []
    rsshub = config.RSSHUB_URL.rstrip("/")

    for path, source_id, name in FEEDS:
        try:
            feed_url = f"{rsshub}{path}"
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
                    "source_category": "industry",
                    "title": title,
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", now_utc_iso()),
                    "raw_body": summary,
                    "original_language": "zh",
                    "metadata": {},
                })
                count += 1
            logger.info(f"Fetched {count} items from {name}")
        except Exception as e:
            logger.warning(f"Failed to fetch {name}: {e}")
    return items
