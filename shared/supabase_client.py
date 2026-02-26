"""
Supabase client wrapper.

Provides CRUD helpers for all tables defined in docs/SCHEMA.md.
"""
import logging
import time
from typing import Optional

from supabase import create_client, Client

from shared import config

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_client() -> Client:
    """Get or create the Supabase client singleton."""
    global _client
    if _client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set")
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def _retry(fn, retries: int = 3, backoff: float = 2.0):
    """Retry a function with exponential backoff."""
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = backoff ** attempt
            logger.warning(f"Retry {attempt + 1}/{retries} after {wait}s: {e}")
            time.sleep(wait)


# --- digest_runs ---

def create_run() -> dict:
    """Create a new digest run record. Returns the created row."""
    def _do():
        return get_client().table("digest_runs").insert({
            "status": "running",
            "items_fetched": 0,
            "items_new": 0,
            "items_scored": 0,
            "sources_succeeded": 0,
            "sources_failed": 0,
            "errors": [],
        }).execute()
    result = _retry(_do)
    return result.data[0]


def update_run(run_id: str, updates: dict) -> None:
    """Update a digest run record."""
    def _do():
        return get_client().table("digest_runs").update(updates).eq("id", run_id).execute()
    _retry(_do)


# --- items ---

def item_exists(content_hash_val: str) -> bool:
    """Check if an item with this content_hash already exists."""
    def _do():
        return get_client().table("items").select("id").eq("content_hash", content_hash_val).limit(1).execute()
    result = _retry(_do)
    return len(result.data) > 0


def insert_items(items: list[dict]) -> int:
    """Insert items into the items table. Returns count of inserted items."""
    if not items:
        return 0
    def _do():
        return get_client().table("items").insert(items).execute()
    result = _retry(_do)
    return len(result.data)


def get_items_by_run(run_id: str) -> list[dict]:
    """Get all items fetched in a specific run (by fetched_at window)."""
    def _do():
        run = get_client().table("digest_runs").select("started_at").eq("id", run_id).single().execute()
        started_at = run.data["started_at"]
        return get_client().table("items").select("*").gte("fetched_at", started_at).order("fetched_at", desc=True).execute()
    result = _retry(_do)
    return result.data


def get_unscored_items(run_id: str) -> list[dict]:
    """Get items from this run that haven't been scored yet."""
    def _do():
        run = get_client().table("digest_runs").select("started_at").eq("id", run_id).single().execute()
        started_at = run.data["started_at"]
        # Get items fetched after this run started that don't have scores for this run
        items = get_client().table("items").select("*").gte("fetched_at", started_at).execute()
        scored = get_client().table("scores").select("item_id").eq("run_id", run_id).execute()
        scored_ids = {s["item_id"] for s in scored.data}
        return type("Result", (), {"data": [i for i in items.data if i["id"] not in scored_ids]})()
    result = _retry(_do)
    return result.data


# --- scores ---

def insert_scores(scores: list[dict]) -> int:
    """Insert score records. Returns count inserted."""
    if not scores:
        return 0
    def _do():
        return get_client().table("scores").insert(scores).execute()
    result = _retry(_do)
    return len(result.data)


def get_top_scored_items(run_id: str, limit: int = 50) -> list[dict]:
    """Get top-scored items for a run, joined with item data."""
    def _do():
        scores = get_client().table("scores").select(
            "*, items(*)"
        ).eq("run_id", run_id).order("total_score", desc=True).limit(limit).execute()
        return scores
    result = _retry(_do)
    return result.data


# --- translations ---

def get_cached_translation(text_hash: str, source_lang: str, target_lang: str = "en") -> Optional[str]:
    """Look up a cached translation."""
    def _do():
        return get_client().table("translations").select("translated_text").eq(
            "text_hash", text_hash
        ).eq("source_language", source_lang).eq("target_language", target_lang).limit(1).execute()
    result = _retry(_do)
    if result.data:
        return result.data[0]["translated_text"]
    return None


# --- multi-day item retrieval ---

def get_unscored_items_since(run_id: str, hours: int = 72) -> list[dict]:
    """Get items from the last N hours that haven't been scored in this run.
    Used for mid-week digests that span multiple fetcher runs.
    Paginates to avoid Supabase's default 1000-row limit."""
    from datetime import datetime, timezone, timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    def _do():
        # Paginate items to get all results beyond Supabase's 1000-row default
        all_items = []
        page_size = 1000
        offset = 0
        while True:
            page = get_client().table("items").select("*").gte(
                "fetched_at", cutoff
            ).order("fetched_at", desc=True).range(offset, offset + page_size - 1).execute()
            all_items.extend(page.data)
            if len(page.data) < page_size:
                break
            offset += page_size

        scored = get_client().table("scores").select("item_id").eq("run_id", run_id).execute()
        scored_ids = {s["item_id"] for s in scored.data}
        return type("Result", (), {
            "data": [i for i in all_items if i["id"] not in scored_ids]
        })()

    result = _retry(_do)
    return result.data


# --- summaries ---

def insert_summaries(summaries: list[dict]) -> int:
    """Batch insert summaries. Returns count inserted."""
    if not summaries:
        return 0
    def _do():
        return get_client().table("summaries").insert(summaries).execute()
    result = _retry(_do)
    return len(result.data)


def get_summaries_by_run(run_id: str) -> dict[str, str]:
    """Get summaries for a run. Returns {item_id: summary}."""
    def _do():
        return get_client().table("summaries").select("item_id, summary").eq("run_id", run_id).execute()
    result = _retry(_do)
    return {row["item_id"]: row["summary"] for row in result.data}


# --- translations ---

def cache_translation(text_hash: str, original_text: str, source_lang: str,
                      translated_text: str, target_lang: str = "en") -> None:
    """Cache a translation result."""
    def _do():
        return get_client().table("translations").upsert({
            "text_hash": text_hash,
            "original_text": original_text,
            "source_language": source_lang,
            "target_language": target_lang,
            "translated_text": translated_text,
        }).execute()
    try:
        _retry(_do)
    except Exception as e:
        logger.warning(f"Failed to cache translation: {e}")
