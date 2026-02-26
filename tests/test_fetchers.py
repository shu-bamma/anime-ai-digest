"""
Tests for individual source fetchers.

Each fetcher should:
1. Return a list (even if empty)
2. Never raise exceptions
3. Return dicts with required keys when successful
"""
import importlib
import os


REQUIRED_KEYS = {"source_id", "source_category", "title", "url", "original_language"}
VALID_CATEGORIES = {"models", "industry", "community", "youtube", "legal"}


def _get_all_fetcher_modules():
    """Discover all fetcher source modules."""
    sources_dir = os.path.join(os.path.dirname(__file__), "..", "agents", "fetcher", "sources")
    modules = []
    for f in sorted(os.listdir(sources_dir)):
        if f.endswith(".py") and f != "__init__.py":
            modules.append(f[:-3])
    return modules


def test_all_fetchers_have_fetch_function():
    """Every source module must expose a fetch() function."""
    for mod_name in _get_all_fetcher_modules():
        mod = importlib.import_module(f"agents.fetcher.sources.{mod_name}")
        assert hasattr(mod, "fetch"), f"{mod_name} missing fetch() function"
        assert callable(mod.fetch), f"{mod_name}.fetch is not callable"


def test_all_fetchers_return_list():
    """Every fetch() must return a list (network calls may fail, but shouldn't raise)."""
    for mod_name in _get_all_fetcher_modules():
        mod = importlib.import_module(f"agents.fetcher.sources.{mod_name}")
        result = mod.fetch()
        assert isinstance(result, list), f"{mod_name}.fetch() returned {type(result)}, expected list"


def test_utils_content_hash():
    """Content hash should be deterministic."""
    from shared.utils import content_hash
    h1 = content_hash("github_wan", "https://example.com", "Test Release")
    h2 = content_hash("github_wan", "https://example.com", "Test Release")
    h3 = content_hash("github_wan", "https://example.com", "Different")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # SHA-256 hex


def test_utils_clean_html():
    """HTML cleaning should strip tags."""
    from shared.utils import clean_html
    assert clean_html("<p>Hello <b>world</b></p>") == "Hello world"
    assert clean_html("") == ""


def test_utils_detect_language():
    """Language detection for CJK."""
    from shared.utils import detect_language
    assert detect_language("Hello world") == "en"
    assert detect_language("AI動画生成モデル") == "ja"
    assert detect_language("AI视频生成模型") == "zh"


def test_utils_truncate():
    """Truncation should respect max length."""
    from shared.utils import truncate
    assert truncate("short", 100) == "short"
    assert len(truncate("a " * 500, 100)) <= 103  # max_len + "..."


def test_models_import():
    """Model TypedDicts should be importable."""
    from shared.models import FetchItem, ScoreResult, DigestRun
    assert FetchItem is not None
    assert ScoreResult is not None
    assert DigestRun is not None
