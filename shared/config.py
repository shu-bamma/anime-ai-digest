"""
Configuration module.

Loads environment variables and defines source configurations,
keyword lists, and scoring weights.
"""
import os
import re
from dotenv import load_dotenv

load_dotenv()

# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# --- Optional API keys ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
RSSHUB_URL = os.getenv("RSSHUB_URL", "https://rsshub.app")

# --- Azure OpenAI ---
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-5.2-chat")

# --- Email delivery (Resend) ---
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
DIGEST_RECIPIENTS: list[str] = [
    r.strip() for r in os.getenv("DIGEST_RECIPIENTS", "").split(",") if r.strip()
]
DIGEST_FROM_EMAIL = os.getenv("DIGEST_FROM_EMAIL", "Anime AI Digest <onboarding@resend.dev>")

# --- Digest window ---
DIGEST_WINDOW_HOURS = int(os.getenv("DIGEST_WINDOW_HOURS", "72"))

# --- GitHub repos to track (owner, repo, source_id) ---
GITHUB_REPOS = [
    ("Wan-AI", "Wan-Video", "github_wan_video"),
    ("bilibili", "Index-AniSora", "github_anisora"),
    ("hpcaitech", "Open-Sora", "github_open_sora"),
    ("Tencent", "HunyuanVideo", "github_hunyuan_video"),
    ("THUDM", "CogVideo", "github_cogvideo"),
    ("Lightricks", "LTX-Video", "github_ltx_video"),
    ("guoyww", "AnimateDiff", "github_animatediff"),
    ("SkyworkAI", "SkyReels-V1", "github_skyreels"),
]

# --- YouTube channels (channel_id, name, source_id) ---
YOUTUBE_CHANNELS = [
    ("UCQCklGPvYEHVKkLqMSL7brA", "SECourses", "youtube_secourses"),
    ("UCScMlXOD6Uf4GiA9TTJxXsA", "Corridor Crew", "youtube_corridor_crew"),
    ("UCxZTjgGkECOemQmSMHnGvkQ", "Next Diffusion", "youtube_next_diffusion"),
    ("UC0EvQB6x1x5qdNbcbD2pugQ", "Banodoco", "youtube_banodoco"),
    ("UCw7BKkyq0OnFk1Eg1UY_R-w", "Digital Creative AI", "youtube_dcai"),
    ("UCjmJDM5pRKbUlVIzDYYWb6g", "Olivio Sarikas", "youtube_olivio_sarikas"),
    ("UCXv2B7rUwMO-kkECJEO0JJg", "The Local Lab AI", "youtube_local_lab_ai"),
]

# --- Reddit subreddits ---
REDDIT_SUBREDDITS = [
    "comfyui",
    "RenPy",
    "SillyTavernAI",
    "WebtoonCanvas",
    "aiRPGofficial",
]

# --- Bilibili search keywords (for RSSHub) ---
BILIBILI_KEYWORDS = [
    "AI动画",
    "AI视频生成",
    "Wan2",
    "AniSora",
    "ComfyUI动画",
]

# --- Keyword lists for filtering and scoring ---
KEYWORDS_HIGH = [
    "anime", "webtoon", "manga", "manhwa", "visual novel",
    "ren'py", "renpy", "twine", "interactive fiction",
    "sakuga", "cel shading", "2d animation", "character consistency",
    "studio ghibli", "anisora", "waifu", "chibi", "shonen", "shojo", "isekai",
]

KEYWORDS_MEDIUM = [
    "wan2", "hunyuanvideo", "cogvideo", "ltx-video", "open-sora",
    "skyreels", "animatediff", "comfyui", "lora", "controlnet",
    "i2v", "t2v", "image-to-video", "text-to-video",
    "video generation", "diffusion", "motion", "temporal",
]

KEYWORDS_LOW = [
    "copyright", "training data", "open source", "apache 2.0",
    "benchmark", "vram", "inference", "model release",
    "fine-tune", "gguf", "fp8", "quantized",
]

ALL_KEYWORDS = KEYWORDS_HIGH + KEYWORDS_MEDIUM + KEYWORDS_LOW

# --- ArXiv keyword filter ---
ARXIV_KEYWORDS = [
    "video generation", "anime", "diffusion video", "temporal consistency",
    "character animation", "style transfer video", "text-to-video",
    "image-to-video", "video diffusion", "motion generation",
]

# --- Japanese keyword filter (for GIGAZINE, etc.) ---
JP_KEYWORDS = [
    "AI", "アニメ", "動画生成", "人工知能", "ビデオ", "画像生成",
    "Wan", "ComfyUI", "Stable Diffusion", "LoRA",
]

# --- Industry news keyword filter ---
NEWS_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "generative",
    "automation", "technology", "production",
    # Anime industry terms that indicate tech/business news
    "studio", "streaming", "Crunchyroll", "Netflix", "Funimation",
    "box office", "acquisition", "merger", "layoff", "funding",
    "copyright", "piracy", "licensing", "simulcast",
    "webtoon", "manhwa", "visual novel",
]

# --- Source priority for scoring ---
SOURCE_PRIORITY = {
    "models": 1.0,
    "community": 0.8,
    "industry": 0.7,
    "youtube": 0.6,
    "legal": 0.5,
}

# --- Scoring weights ---
SCORING_WEIGHTS = {
    "recency": 0.25,
    "engagement": 0.25,
    "keyword_relevance": 0.30,
    "source_priority": 0.20,
}

# --- Per-source cap ---
MAX_ITEMS_PER_SOURCE = int(os.getenv("MAX_ITEMS_PER_SOURCE", "8"))

# --- Minimum items for digest ---
MIN_ITEMS_FOR_DIGEST = int(os.getenv("MIN_ITEMS_FOR_DIGEST", "3"))

# --- Fetch settings ---
REQUEST_TIMEOUT = 30  # seconds
USER_AGENT = "anime-ai-digest/1.0 (+https://github.com/shu-bamma/anime-ai-digest)"


# --- Word-boundary keyword matching ---

def _word_boundary_match(keyword: str, text: str) -> bool:
    """Check if keyword matches as a whole word (not substring) in text."""
    return bool(re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE))


def keyword_in_text(keywords: list[str], text: str) -> int:
    """Count how many keywords match using word boundaries. Avoids false positives
    like 'AI' matching 'email', 'detail', 'fair', etc."""
    return sum(1 for kw in keywords if _word_boundary_match(kw, text))
