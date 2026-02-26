"""
Source fetcher: civitai — CivitAI REST API for anime video LoRAs.

See docs/SOURCE_EXPLORATION.md §3a for details.
"""
import logging

import requests

from shared import config
from shared.utils import now_utc_iso, truncate

logger = logging.getLogger(__name__)

API_BASE = "https://civitai.com/api/v1/models"
ANIME_TAGS = ["anime", "wan", "video", "webtoon", "animation"]


def _fetch_page(params: dict) -> list[dict]:
    """Fetch a single page from CivitAI API."""
    resp = requests.get(API_BASE, params=params, timeout=config.REQUEST_TIMEOUT, headers={
        "User-Agent": config.USER_AGENT,
    })
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", [])


def fetch() -> list[dict]:
    """Fetch trending anime/video LoRAs from CivitAI."""
    items = []
    try:
        # Newest anime LoRAs
        for tag in ANIME_TAGS:
            try:
                models = _fetch_page({
                    "sort": "Newest",
                    "types": "LORA",
                    "tag": tag,
                    "limit": 10,
                })
                for model in models:
                    name = model.get("name", "")
                    model_id = model.get("id", "")
                    stats = model.get("stats", {})
                    items.append({
                        "source_id": "civitai_lora",
                        "source_category": "community",
                        "title": name,
                        "url": f"https://civitai.com/models/{model_id}",
                        "published_at": model.get("publishedAt", model.get("createdAt", now_utc_iso())),
                        "raw_body": truncate(model.get("description", "") or "", 500),
                        "original_language": "en",
                        "metadata": {
                            "downloads": stats.get("downloadCount", 0),
                            "rating": stats.get("rating", 0),
                            "favorites": stats.get("favoriteCount", 0),
                            "tags": [t.get("name", "") for t in model.get("tags", [])],
                            "creator": model.get("creator", {}).get("username", ""),
                        },
                    })
            except Exception as e:
                logger.warning(f"CivitAI tag '{tag}' fetch failed: {e}")

        # Deduplicate by model URL
        seen = set()
        deduped = []
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                deduped.append(item)
        items = deduped

        logger.info(f"Fetched {len(items)} models from CivitAI")
    except Exception as e:
        logger.error(f"Failed to fetch CivitAI: {e}")
    return items
