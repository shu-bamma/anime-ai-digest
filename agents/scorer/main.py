"""
Scorer Agent — computes relevance scores for fetched items.

Reads items from Supabase, applies weighted scoring, writes scores back.

See docs/AGENTS.md for the full contract and scoring weights.

Usage:
    python -m agents.scorer.main --run-id <uuid>
"""
import logging

logger = logging.getLogger(__name__)


def run_scorer(run_id: str) -> dict:
    """Score all items from a given digest run. See docs/AGENTS.md for contract."""
    # TODO: Implement
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not run_id:
        logger.error("Usage: python -m agents.scorer.main <run_id>")
        sys.exit(1)
    result = run_scorer(run_id)
    logger.info(f"Scorer complete: {result}")
