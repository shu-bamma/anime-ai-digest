"""
Emailer Agent — sends the digest via Resend to configured recipients.

Uses RESEND_API_KEY, DIGEST_RECIPIENTS, and DIGEST_FROM_EMAIL from environment.
"""
import logging
from datetime import datetime, timezone
from pathlib import Path

import resend

from shared import config

logger = logging.getLogger(__name__)


def run_emailer(html_path: str, date_str: str | None = None) -> dict:
    """Send the digest HTML to all configured recipients via Resend."""
    if not config.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — skipping email delivery")
        return {"sent": 0, "skipped": True}

    recipients = config.DIGEST_RECIPIENTS
    if not recipients:
        logger.warning("DIGEST_RECIPIENTS not configured — skipping email delivery")
        return {"sent": 0, "skipped": True}

    if not config.DIGEST_FROM_EMAIL:
        logger.warning("DIGEST_FROM_EMAIL not configured — skipping email delivery")
        return {"sent": 0, "skipped": True}

    html_content = Path(html_path).read_text(encoding="utf-8")
    if not date_str:
        date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    resend.api_key = config.RESEND_API_KEY

    sent = 0
    errors = []
    for recipient in recipients:
        try:
            resend.Emails.send({
                "from": config.DIGEST_FROM_EMAIL,
                "to": recipient.strip(),
                "subject": f"The Anime AI Digest — {date_str}",
                "html": html_content,
            })
            sent += 1
            logger.info(f"Sent digest to {recipient}")
        except Exception as e:
            logger.error(f"Failed to send to {recipient}: {e}")
            errors.append({"recipient": recipient, "error": str(e)})

    return {"sent": sent, "errors": errors}


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        logger.error("Usage: python -m agents.emailer.main <html_path>")
        sys.exit(1)
    result = run_emailer(sys.argv[1])
    logger.info(f"Emailer complete: {result}")
