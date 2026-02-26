"""
Source fetcher: legal_policy — CODA and METI scraping (weekly).

See docs/SOURCE_EXPLORATION.md §5 for details.
"""
import logging

import requests
from bs4 import BeautifulSoup

from shared import config

logger = logging.getLogger(__name__)

SOURCES = [
    ("https://www.coda-cjk.jp/en/", "coda_jp", "CODA"),
    ("https://www.meti.go.jp/english/press/index.html", "meti_jp", "METI"),
]

KEYWORDS = ["ai", "copyright", "training data", "generative", "content",
            "creative", "anime", "artificial intelligence"]


def _matches_keywords(text: str) -> bool:
    return config.keyword_in_text(KEYWORDS, text) > 0


def fetch() -> list[dict]:
    """Scrape CODA and METI for AI copyright/policy news."""
    items = []
    for url, source_id, name in SOURCES:
        try:
            resp = requests.get(url, timeout=config.REQUEST_TIMEOUT, headers={
                "User-Agent": config.USER_AGENT,
            })
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Generic link extraction from news/press sections
            for a_tag in soup.select("a"):
                text = a_tag.get_text(strip=True)
                href = a_tag.get("href", "")
                if not text or not href or len(text) < 10:
                    continue
                if not _matches_keywords(text):
                    continue
                # Resolve relative URLs
                if href.startswith("/"):
                    from urllib.parse import urljoin
                    href = urljoin(url, href)
                items.append({
                    "source_id": source_id,
                    "source_category": "legal",
                    "title": text[:200],
                    "url": href,
                    "published_at": None,  # No date available from scrape; Supabase defaults
                    "raw_body": "",
                    "original_language": "en",
                    "metadata": {"source_org": name},
                })
            logger.info(f"Fetched {len([i for i in items if i['source_id'] == source_id])} items from {name}")
        except Exception as e:
            logger.error(f"Failed to scrape {name}: {e}")
    return items
