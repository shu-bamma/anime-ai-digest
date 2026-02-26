"""
Fetcher Agent — orchestrates all source fetchers.

Runs each source fetcher, deduplicates items, translates CJK content,
and stores results in Supabase.

See docs/AGENTS.md for the full contract.
"""
import logging
from datetime import datetime, timezone

from shared import supabase_client
from shared.utils import content_hash, now_utc_iso
from shared.translator import translate_item

from agents.fetcher.sources import (
    github_releases,
    huggingface,
    arxiv,
    anime_news,
    youtube_rss,
    reddit_rss,
    itchio,
    civitai,
    comfyui_nodes,
    sakugabooru,
    bilibili,
    chinese_ai_news,
    anime_corner,
    gigazine,
    legal_policy,
    pixiv,
    clip_studio,
    lemmasoft,
)

logger = logging.getLogger(__name__)

# All source fetchers in execution order (most reliable first)
FETCHERS = [
    ("github_releases", github_releases),
    ("huggingface", huggingface),
    ("arxiv", arxiv),
    ("anime_news", anime_news),
    ("youtube_rss", youtube_rss),
    ("reddit_rss", reddit_rss),
    ("itchio", itchio),
    ("civitai", civitai),
    ("comfyui_nodes", comfyui_nodes),
    ("sakugabooru", sakugabooru),
    ("bilibili", bilibili),
    ("chinese_ai_news", chinese_ai_news),
    ("anime_corner", anime_corner),
    ("gigazine", gigazine),
    ("legal_policy", legal_policy),
    ("pixiv", pixiv),
    ("clip_studio", clip_studio),
    ("lemmasoft", lemmasoft),
]


def run_fetcher() -> dict:
    """Run all enabled source fetchers. See docs/AGENTS.md for contract."""
    # 1. Create a digest_run record
    run = supabase_client.create_run()
    run_id = run["id"]
    logger.info(f"Created digest run: {run_id}")

    all_items = []
    errors = []
    sources_succeeded = 0
    sources_failed = 0

    # 2. Run each fetcher
    for name, module in FETCHERS:
        try:
            logger.info(f"Running fetcher: {name}")
            fetched = module.fetch()
            all_items.extend(fetched)
            sources_succeeded += 1
            logger.info(f"  {name}: {len(fetched)} items")
        except Exception as e:
            sources_failed += 1
            error_info = {
                "source_id": name,
                "error": str(e),
                "timestamp": now_utc_iso(),
            }
            errors.append(error_info)
            logger.error(f"  {name} FAILED: {e}")

    items_fetched = len(all_items)
    logger.info(f"Total items fetched: {items_fetched}")

    # 3. Deduplicate against existing items
    new_items = []
    for item in all_items:
        ch = content_hash(
            item.get("source_id", ""),
            item.get("url", ""),
            item.get("title", ""),
        )
        item["content_hash"] = ch
        item["fetched_at"] = now_utc_iso()

        if not supabase_client.item_exists(ch):
            new_items.append(item)

    logger.info(f"New items after dedup: {len(new_items)}")

    # 4. Translate non-English items
    for item in new_items:
        if item.get("original_language", "en") != "en":
            try:
                translate_item(item)
            except Exception as e:
                logger.warning(f"Translation failed for item: {e}")

    # 5. Insert into Supabase
    inserted = 0
    if new_items:
        # Insert in batches of 50
        for i in range(0, len(new_items), 50):
            batch = new_items[i:i + 50]
            try:
                inserted += supabase_client.insert_items(batch)
            except Exception as e:
                logger.error(f"Failed to insert batch {i}: {e}")

    # 6. Update run stats
    supabase_client.update_run(run_id, {
        "items_fetched": items_fetched,
        "items_new": inserted,
        "sources_succeeded": sources_succeeded,
        "sources_failed": sources_failed,
        "errors": errors,
        "status": "completed" if sources_failed == 0 else "partial",
    })

    result = {
        "run_id": run_id,
        "items_fetched": items_fetched,
        "items_new": inserted,
        "sources_succeeded": sources_succeeded,
        "sources_failed": sources_failed,
        "errors": errors,
    }
    logger.info(f"Fetcher complete: {result}")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_fetcher()
    logger.info(f"Fetcher complete: {result}")
