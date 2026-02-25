"""
Configuration module.

Loads environment variables and defines source configurations,
keyword lists, and scoring weights.

See docs/SOURCE_EXPLORATION.md for details on each source.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # service role key

# --- Optional API keys ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
RSSHUB_URL = os.getenv("RSSHUB_URL", "https://rsshub.app")  # default to public instance

# --- Source definitions ---
# TODO: Implement. See docs/SOURCE_EXPLORATION.md for all sources and their endpoints.
# Each source should have: id, name, category, fetch_method, url, enabled, frequency

GITHUB_REPOS = [
    # TODO: populate with (owner, repo, source_id) tuples
    # e.g. ("Wan-AI", "Wan-Video", "github_wan_video"),
]

YOUTUBE_CHANNEL_IDS = [
    # TODO: populate with (channel_id, name, source_id) tuples
    # Look up channel IDs during implementation
]

REDDIT_SUBREDDITS = [
    "comfyui",
    "RenPy",
    "SillyTavernAI",
    "WebtoonCanvas",
    "aiRPGofficial",
]

# --- Keyword lists for filtering and scoring ---
# TODO: Implement. See docs/AGENTS.md for suggested keyword categories.

# --- Scoring weights ---
SCORING_WEIGHTS = {
    "recency": 0.25,
    "engagement": 0.25,
    "keyword_relevance": 0.30,
    "source_priority": 0.20,
}
