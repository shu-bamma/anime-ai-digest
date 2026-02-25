"""
Source fetcher: arxiv

See docs/SOURCE_EXPLORATION.md for endpoint details, rate limits, and auth requirements.
See docs/AGENTS.md for the fetch() contract.

Returns list[dict] of FetchItem dicts. Returns [] on failure.
"""
import logging

logger = logging.getLogger(__name__)


def fetch() -> list[dict]:
    """Fetch items from arxiv. See docs/AGENTS.md for return format."""
    # TODO: Implement — consult docs/SOURCE_EXPLORATION.md for this source
    logger.warning("arxiv fetcher not implemented yet")
    return []
