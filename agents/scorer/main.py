"""
Scorer Agent — computes relevance scores for fetched items.

Reads items from Supabase, applies weighted scoring, writes scores back.
See docs/AGENTS.md for the full contract and scoring weights.
"""
import logging
import math
from datetime import datetime, timezone

from shared import config, supabase_client
from shared.utils import parse_date

logger = logging.getLogger(__name__)


def _recency_score(published_at: str | None) -> float:
    """Score based on how recent the item is. 0-1, higher = newer."""
    if not published_at:
        return 0.3  # Unknown date gets a middling score
    dt = parse_date(published_at)
    if not dt:
        return 0.3
    now = datetime.now(timezone.utc)
    hours_ago = (now - dt).total_seconds() / 3600
    if hours_ago <= 0:
        return 1.0
    if hours_ago <= 24:
        return 1.0 - (hours_ago / 48)  # 0.5-1.0 for last 24h
    if hours_ago <= 72:
        return 0.5 - ((hours_ago - 24) / 96)  # 0.25-0.5 for 1-3 days
    if hours_ago <= 168:
        return 0.25 - ((hours_ago - 72) / 384)  # 0.0-0.25 for 3-7 days
    return 0.0


def _engagement_score(metadata: dict) -> float:
    """Score based on engagement metrics (stars, downloads, etc.). 0-1."""
    score = 0.0
    stars = metadata.get("stars", 0)
    downloads = metadata.get("downloads", 0)
    favorites = metadata.get("favorites", 0)
    rating = metadata.get("rating", 0)
    booru_score = metadata.get("score", 0)

    # Logarithmic scaling for various metrics
    if stars:
        score = max(score, min(1.0, math.log10(max(stars, 1)) / 5))  # 100k stars = 1.0
    if downloads:
        score = max(score, min(1.0, math.log10(max(downloads, 1)) / 5))
    if favorites:
        score = max(score, min(1.0, math.log10(max(favorites, 1)) / 4))
    if rating and rating > 0:
        score = max(score, rating / 5.0)
    if booru_score:
        score = max(score, min(1.0, booru_score / 50.0))

    return score


def _keyword_score(title: str, body: str) -> float:
    """Score based on keyword relevance. 0-1."""
    text = f"{title} {body}".lower()
    score = 0.0

    high_matches = config.keyword_in_text(config.KEYWORDS_HIGH, text)
    med_matches = config.keyword_in_text(config.KEYWORDS_MEDIUM, text)
    low_matches = config.keyword_in_text(config.KEYWORDS_LOW, text)

    # Weighted keyword presence
    score += min(high_matches * 0.15, 0.6)
    score += min(med_matches * 0.08, 0.3)
    score += min(low_matches * 0.04, 0.1)

    return min(score, 1.0)


def _source_priority_score(source_category: str) -> float:
    """Score based on source category priority. 0-1."""
    return config.SOURCE_PRIORITY.get(source_category, 0.5)


def run_scorer(run_id: str) -> dict:
    """Score all items from a given digest run."""
    items = supabase_client.get_unscored_items_since(run_id, hours=config.DIGEST_WINDOW_HOURS)
    logger.info(f"Scoring {len(items)} items for run {run_id}")

    weights = config.SCORING_WEIGHTS
    scores_to_insert = []

    for item in items:
        title = item.get("title", "")
        body = item.get("raw_body", "") or ""
        title_translated = item.get("title_translated", "")
        body_translated = item.get("body_translated", "")
        # Use translated text for keyword matching if available
        search_title = title_translated or title
        search_body = body_translated or body

        r_score = _recency_score(item.get("published_at"))
        e_score = _engagement_score(item.get("metadata", {}))
        k_score = _keyword_score(search_title, search_body)
        s_score = _source_priority_score(item.get("source_category", ""))

        total = (
            weights["recency"] * r_score +
            weights["engagement"] * e_score +
            weights["keyword_relevance"] * k_score +
            weights["source_priority"] * s_score
        )

        scores_to_insert.append({
            "item_id": item["id"],
            "run_id": run_id,
            "total_score": round(total, 4),
            "recency_score": round(r_score, 4),
            "engagement_score": round(e_score, 4),
            "keyword_score": round(k_score, 4),
            "source_priority_score": round(s_score, 4),
        })

    # Insert scores in batches
    inserted = 0
    for i in range(0, len(scores_to_insert), 50):
        batch = scores_to_insert[i:i + 50]
        try:
            inserted += supabase_client.insert_scores(batch)
        except Exception as e:
            logger.error(f"Failed to insert score batch: {e}")

    # Update run
    supabase_client.update_run(run_id, {"items_scored": inserted})

    result = {"items_scored": inserted}
    logger.info(f"Scorer complete: {result}")
    return result


def apply_source_cap(scored_items: list[dict], max_per_source: int | None = None) -> list[dict]:
    """Apply per-source cap and ensure category diversity.
    Items should already be sorted by score descending.

    Strategy:
    1. First pass: pick top items per category (min 3 per non-empty category)
    2. Fill remaining slots from the overall ranked list with per-source cap
    """
    cap = max_per_source or config.MAX_ITEMS_PER_SOURCE
    min_per_category = 3

    # Group by category preserving score order
    by_category: dict[str, list[dict]] = {}
    for item_row in scored_items:
        item = item_row.get("items", item_row)
        cat = item.get("source_category", "community")
        by_category.setdefault(cat, []).append(item_row)

    # Phase 1: Reserve minimum slots per category
    reserved_ids: set[str] = set()
    result: list[dict] = []
    source_counts: dict[str, int] = {}

    for cat, cat_items in by_category.items():
        added = 0
        for item_row in cat_items:
            if added >= min_per_category:
                break
            item = item_row.get("items", item_row)
            source = item.get("source_id", "unknown")
            item_id = item.get("id", "")
            if source_counts.get(source, 0) >= cap:
                continue
            result.append(item_row)
            reserved_ids.add(item_id)
            source_counts[source] = source_counts.get(source, 0) + 1
            added += 1

    # Phase 2: Fill remaining from overall ranked list
    for item_row in scored_items:
        item = item_row.get("items", item_row)
        item_id = item.get("id", "")
        if item_id in reserved_ids:
            continue
        source = item.get("source_id", "unknown")
        if source_counts.get(source, 0) >= cap:
            continue
        source_counts[source] = source_counts.get(source, 0) + 1
        result.append(item_row)
        reserved_ids.add(item_id)

    # Re-sort by total_score descending
    result.sort(key=lambda r: r.get("total_score", 0), reverse=True)
    return result


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not run_id:
        logger.error("Usage: python -m agents.scorer.main <run_id>")
        sys.exit(1)
    result = run_scorer(run_id)
    logger.info(f"Scorer complete: {result}")
