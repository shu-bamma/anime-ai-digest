"""
Source fetcher: lemmasoft — Lemmasoft Visual Novel Forums (weekly).

See docs/SOURCE_EXPLORATION.md §3g for details.
"""
import logging

import feedparser
import requests
from bs4 import BeautifulSoup

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)

FORUM_URL = "https://lemmasoft.renai.us/forums/"
FEED_URL = "https://lemmasoft.renai.us/forums/feed"

KEYWORDS = ["ai", "artificial intelligence", "generative", "machine learning",
            "stable diffusion", "comfyui", "animation"]


def _matches_keywords(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)


def fetch() -> list[dict]:
    """Fetch AI-related threads from Lemmasoft forums."""
    items = []

    # Try RSS feed first
    try:
        resp = requests.get(FEED_URL, timeout=config.REQUEST_TIMEOUT, headers={
            "User-Agent": config.USER_AGENT,
        })
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        if feed.entries:
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                if not _matches_keywords(f"{title} {summary}"):
                    continue
                items.append({
                    "source_id": "lemmasoft",
                    "source_category": "community",
                    "title": title,
                    "url": entry.get("link", ""),
                    "published_at": entry.get("published", now_utc_iso()),
                    "raw_body": summary,
                    "original_language": "en",
                    "metadata": {},
                })
            logger.info(f"Fetched {len(items)} relevant posts from Lemmasoft (RSS)")
            return items
    except Exception as e:
        logger.debug(f"Lemmasoft RSS failed, trying scrape: {e}")

    # Fallback: scrape forum index
    try:
        resp = requests.get(FORUM_URL, timeout=config.REQUEST_TIMEOUT, headers={
            "User-Agent": config.USER_AGENT,
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        for a_tag in soup.select("a.topictitle"):
            title = a_tag.get_text(strip=True)
            href = a_tag.get("href", "")
            if not _matches_keywords(title):
                continue
            if href.startswith("./"):
                href = f"{FORUM_URL}{href[2:]}"
            items.append({
                "source_id": "lemmasoft",
                "source_category": "community",
                "title": title,
                "url": href,
                "published_at": now_utc_iso(),
                "raw_body": "",
                "original_language": "en",
                "metadata": {},
            })
        logger.info(f"Fetched {len(items)} relevant posts from Lemmasoft (scrape)")
    except Exception as e:
        logger.error(f"Failed to scrape Lemmasoft: {e}")
    return items
