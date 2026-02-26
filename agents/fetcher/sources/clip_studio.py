"""
Source fetcher: clip_studio — Clip Studio Tips scrape (weekly).

See docs/SOURCE_EXPLORATION.md §3f for details.
"""
import logging
import re

import requests
from bs4 import BeautifulSoup

from shared import config

logger = logging.getLogger(__name__)

TIPS_URL = "https://tips.clip-studio.com/en-us/"

KEYWORDS = ["ai", "animation", "webtoon", "video", "automatic"]


def _matches_keywords(text: str) -> bool:
    return config.keyword_in_text(KEYWORDS, text) > 0


def fetch() -> list[dict]:
    """Scrape Clip Studio Tips for AI/animation articles."""
    items = []
    try:
        resp = requests.get(TIPS_URL, timeout=config.REQUEST_TIMEOUT, headers={
            "User-Agent": config.USER_AGENT,
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        for a_tag in soup.select("a[href*='/articles/']"):
            raw_text = a_tag.get_text(strip=True)
            # Strip trailing numeric stats (views/likes) that BS4 captures from sibling spans
            text = re.sub(r'[\d,]{3,}$', '', raw_text).strip()
            text = re.sub(r'[\d,]{3,}$', '', text).strip()  # Second pass for multiple stat blocks
            href = a_tag.get("href", "")
            if not text or len(text) < 5:
                continue
            if not _matches_keywords(text):
                continue
            if href.startswith("/"):
                href = f"https://tips.clip-studio.com{href}"
            items.append({
                "source_id": "clip_studio",
                "source_category": "community",
                "title": text[:200],
                "url": href,
                "published_at": None,  # No date on scraped page; Supabase defaults
                "raw_body": "",
                "original_language": "en",
                "metadata": {},
            })
        logger.info(f"Fetched {len(items)} relevant articles from Clip Studio Tips")
    except Exception as e:
        logger.error(f"Failed to scrape Clip Studio Tips: {e}")
    return items
