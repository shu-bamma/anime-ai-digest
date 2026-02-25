"""
Renderer Agent — generates daily digest (Markdown + HTML).

Reads top-scored items from Supabase, groups by category, renders output.

See docs/AGENTS.md for the full contract and digest structure.

Usage:
    python -m agents.renderer.main --run-id <uuid>
"""
import logging

logger = logging.getLogger(__name__)


def run_renderer(run_id: str) -> dict:
    """Generate daily digest from scored items. See docs/AGENTS.md for contract."""
    # TODO: Implement
    raise NotImplementedError


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not run_id:
        logger.error("Usage: python -m agents.renderer.main <run_id>")
        sys.exit(1)
    result = run_renderer(run_id)
    logger.info(f"Renderer complete: {result}")
