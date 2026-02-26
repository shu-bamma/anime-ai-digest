"""
Data models / TypedDicts for the pipeline.

Defines the shape of data passed between agents.
See docs/AGENTS.md for the FetchItem contract.
"""
from typing import TypedDict, Optional


class FetchItem(TypedDict, total=False):
    source_id: str
    source_category: str  # "models", "industry", "community", "youtube", "legal"
    title: str
    url: str
    published_at: Optional[str]  # ISO 8601 UTC
    raw_body: Optional[str]
    original_language: str  # ISO 639-1: "en", "ja", "zh", "ko"
    metadata: dict


class ScoreResult(TypedDict):
    item_id: str
    run_id: str
    total_score: float
    recency_score: float
    engagement_score: float
    keyword_score: float
    source_priority_score: float


class DigestRun(TypedDict, total=False):
    id: str
    started_at: str
    completed_at: Optional[str]
    status: str  # "running", "completed", "failed"
    items_fetched: int
    items_new: int
    items_scored: int
    sources_succeeded: int
    sources_failed: int
    errors: list
    output_md: Optional[str]
    output_html: Optional[str]
