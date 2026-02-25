"""
Pipeline orchestrator — runs fetcher → scorer → renderer sequentially.

Usage:
    python run.py
"""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("pipeline")


def main():
    logger.info("=== Anime AI Video Digest Pipeline ===")

    # Step 1: Fetch
    from agents.fetcher.main import run_fetcher
    logger.info("--- FETCHER ---")
    fetch_result = run_fetcher()
    run_id = fetch_result.get("run_id")
    logger.info(f"Fetch complete: {fetch_result}")

    if not run_id:
        logger.error("No run_id returned from fetcher. Aborting.")
        sys.exit(1)

    # Step 2: Score
    from agents.scorer.main import run_scorer
    logger.info("--- SCORER ---")
    score_result = run_scorer(run_id)
    logger.info(f"Score complete: {score_result}")

    # Step 3: Render
    from agents.renderer.main import run_renderer
    logger.info("--- RENDERER ---")
    render_result = run_renderer(run_id)
    logger.info(f"Render complete: {render_result}")

    logger.info("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
