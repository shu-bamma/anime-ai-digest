"""
Source fetcher: comfyui_nodes — ComfyUI Manager node list diff.

Fetches the ComfyUI Manager custom-node-list.json and reports new entries.
See docs/SOURCE_EXPLORATION.md §3b for details.
"""
import json
import logging

import requests

from shared import config

logger = logging.getLogger(__name__)

NODE_LIST_URL = "https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main/custom-node-list.json"

ANIME_KEYWORDS = ["anime", "video", "wan", "animation", "i2v", "t2v",
                   "lora", "motion", "temporal", "diffusion"]


def _matches_keywords(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in ANIME_KEYWORDS)


def fetch() -> list[dict]:
    """Fetch new ComfyUI custom nodes relevant to anime/video."""
    items = []
    try:
        resp = requests.get(NODE_LIST_URL, timeout=config.REQUEST_TIMEOUT, headers={
            "User-Agent": config.USER_AGENT,
        })
        resp.raise_for_status()
        data = resp.json()
        nodes = data.get("custom_nodes", data) if isinstance(data, dict) else data

        for node in nodes:
            if not isinstance(node, dict):
                continue
            title = node.get("title", "") or node.get("name", "")
            desc = node.get("description", "")
            reference = node.get("reference", "")
            if not _matches_keywords(f"{title} {desc}"):
                continue
            # Parse actual last_update field; fall back to None (Supabase default)
            last_update = node.get("last_update") or None
            items.append({
                "source_id": "comfyui_nodes",
                "source_category": "community",
                "title": title,
                "url": reference or "",
                "published_at": last_update,
                "raw_body": desc,
                "original_language": "en",
                "metadata": {
                    "author": node.get("author", ""),
                    "install_type": node.get("install_type", ""),
                },
            })
        # Cap to avoid dominating the digest
        items = items[:30]
        logger.info(f"Found {len(items)} relevant ComfyUI nodes (capped at 30)")
    except Exception as e:
        logger.error(f"Failed to fetch ComfyUI node list: {e}")
    return items
