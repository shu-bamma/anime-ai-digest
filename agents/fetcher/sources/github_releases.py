"""
Source fetcher: github_releases — 8 repo Atom feeds.

See docs/SOURCE_EXPLORATION.md §1a for details.
"""
import logging

import feedparser
import requests

from shared import config
from shared.utils import clean_html, now_utc_iso

logger = logging.getLogger(__name__)


def fetch() -> list[dict]:
    """Fetch latest releases from tracked GitHub repos via Atom feeds."""
    items = []
    for owner, repo, source_id in config.GITHUB_REPOS:
        try:
            feed_url = f"https://github.com/{owner}/{repo}/releases.atom"
            resp = requests.get(feed_url, timeout=config.REQUEST_TIMEOUT, headers={
                "User-Agent": config.USER_AGENT,
            })
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)

            for entry in feed.entries[:5]:
                body = ""
                if entry.get("content"):
                    body = clean_html(entry.content[0].get("value", ""))
                items.append({
                    "source_id": source_id,
                    "source_category": "models",
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published_at": entry.get("updated", entry.get("published", now_utc_iso())),
                    "raw_body": body,
                    "original_language": "en",
                    "metadata": {
                        "repo": f"{owner}/{repo}",
                        "tag": entry.get("id", "").split("/")[-1] if entry.get("id") else "",
                    },
                })
            logger.info(f"Fetched {min(len(feed.entries), 5)} releases from {owner}/{repo}")
        except Exception as e:
            logger.error(f"Failed to fetch {owner}/{repo}: {e}")
    return items
