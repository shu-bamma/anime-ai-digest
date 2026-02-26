"""
Source fetcher: sakugabooru — Booru JSON API.

See docs/SOURCE_EXPLORATION.md §3d for details.
"""
import logging

import requests

from shared import config

logger = logging.getLogger(__name__)

API_URL = "https://www.sakugabooru.com/post.json"


def fetch() -> list[dict]:
    """Fetch AI-tagged posts from Sakugabooru."""
    items = []
    try:
        resp = requests.get(API_URL, params={
            "tags": "ai animated",
            "limit": 20,
        }, timeout=config.REQUEST_TIMEOUT, headers={
            "User-Agent": config.USER_AGENT,
        })
        resp.raise_for_status()
        posts = resp.json()

        for post in posts:
            post_id = post.get("id", "")
            tags = post.get("tags", "")
            source_url = post.get("source", "")
            # Parse actual created_at from API response
            created_at = post.get("created_at") or None
            items.append({
                "source_id": "sakugabooru",
                "source_category": "community",
                "title": f"Sakugabooru #{post_id}: {tags[:80]}",
                "url": f"https://www.sakugabooru.com/post/show/{post_id}",
                "published_at": created_at,
                "raw_body": f"Tags: {tags}\nSource: {source_url}",
                "original_language": "en",
                "metadata": {
                    "score": post.get("score", 0),
                    "tags": tags,
                    "source_url": source_url,
                },
            })
        logger.info(f"Fetched {len(items)} posts from Sakugabooru")
    except Exception as e:
        logger.error(f"Failed to fetch Sakugabooru: {e}")
    return items
