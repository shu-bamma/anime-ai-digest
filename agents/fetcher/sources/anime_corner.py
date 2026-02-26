"""
Source fetcher: anime_corner — WordPress scrape.

See docs/SOURCE_EXPLORATION.md §2b for details.
"""
import logging

import requests
from bs4 import BeautifulSoup

from shared import config
from shared.utils import now_utc_iso

logger = logging.getLogger(__name__)

NEWS_URL = "https://animecorner.me/category/news/"


def _matches_keywords(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in config.NEWS_KEYWORDS)


def fetch() -> list[dict]:
    """Scrape Anime Corner news page for AI/technology articles."""
    items = []
    try:
        resp = requests.get(NEWS_URL, timeout=config.REQUEST_TIMEOUT, headers={
            "User-Agent": config.USER_AGENT,
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        articles = soup.select("article")
        for article in articles[:20]:
            title_el = article.select_one("h2 a, .entry-title a, h3 a")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            excerpt_el = article.select_one(".entry-excerpt, .entry-summary, p")
            excerpt = excerpt_el.get_text(strip=True) if excerpt_el else ""
            date_el = article.select_one("time")
            published = date_el.get("datetime", now_utc_iso()) if date_el else now_utc_iso()

            if not _matches_keywords(f"{title} {excerpt}"):
                continue

            items.append({
                "source_id": "anime_corner",
                "source_category": "industry",
                "title": title,
                "url": url,
                "published_at": published,
                "raw_body": excerpt,
                "original_language": "en",
                "metadata": {},
            })
        logger.info(f"Fetched {len(items)} relevant articles from Anime Corner")
    except Exception as e:
        logger.error(f"Failed to scrape Anime Corner: {e}")
    return items
