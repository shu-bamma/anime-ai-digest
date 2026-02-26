"""
Pipeline orchestrator — runs fetcher → scorer → summarizer → renderer → emailer.

Usage:
    python run.py
"""
import logging
import sys

from shared import config

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
    try:
        fetch_result = run_fetcher()
    except Exception as e:
        logger.error(f"Fetcher crashed: {e}")
        sys.exit(1)

    run_id = fetch_result.get("run_id")
    logger.info(f"Fetch complete: {fetch_result}")

    if not run_id:
        logger.error("No run_id returned from fetcher. Aborting.")
        sys.exit(1)

    items_new = fetch_result.get("items_new", 0)
    if items_new < config.MIN_ITEMS_FOR_DIGEST:
        logger.warning(f"Only {items_new} new items (min {config.MIN_ITEMS_FOR_DIGEST}). Skipping digest.")
        from shared import supabase_client
        supabase_client.update_run(run_id, {"status": "skipped_insufficient_items"})
        return

    # Step 2: Score
    from agents.scorer.main import run_scorer
    logger.info("--- SCORER ---")
    try:
        score_result = run_scorer(run_id)
        logger.info(f"Score complete: {score_result}")
    except Exception as e:
        logger.error(f"Scorer failed: {e}")
        from shared import supabase_client
        supabase_client.update_run(run_id, {"status": "failed", "errors": [{"agent": "scorer", "error": str(e)}]})
        sys.exit(1)

    # Step 3: Summarize
    from agents.summarizer.main import run_summarizer
    logger.info("--- SUMMARIZER ---")
    try:
        summary_result = run_summarizer(run_id)
        logger.info(f"Summarize complete: {summary_result}")
    except Exception as e:
        logger.error(f"Summarizer failed: {e}")
        from shared import supabase_client
        supabase_client.update_run(run_id, {"status": "failed", "errors": [{"agent": "summarizer", "error": str(e)}]})
        sys.exit(1)

    # Step 4: Render
    from agents.renderer.main import run_renderer
    logger.info("--- RENDERER ---")
    try:
        render_result = run_renderer(run_id, summary_data=summary_result)
        logger.info(f"Render complete: {render_result}")
    except Exception as e:
        logger.error(f"Renderer failed: {e}")
        from shared import supabase_client
        supabase_client.update_run(run_id, {"status": "failed", "errors": [{"agent": "renderer", "error": str(e)}]})
        sys.exit(1)

    # Step 5: Email
    from agents.emailer.main import run_emailer
    logger.info("--- EMAILER ---")
    html_path = render_result.get("html_path", "")
    if html_path:
        try:
            email_result = run_emailer(html_path)
            logger.info(f"Email complete: {email_result}")
        except Exception as e:
            logger.error(f"Emailer failed: {e}")
    else:
        logger.warning("No HTML path from renderer, skipping email")

    logger.info("=== Pipeline complete ===")


if __name__ == "__main__":
    main()
