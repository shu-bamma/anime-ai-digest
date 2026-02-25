"""
Tests for individual source fetchers.

Each fetcher should:
1. Return a list (even if empty)
2. Never raise exceptions
3. Return dicts with required keys when successful

TODO: Add tests for each implemented fetcher.
      Use mocked responses to avoid hitting real APIs in CI.
"""
import importlib
import os


def _get_all_fetcher_modules():
    """Discover all fetcher source modules."""
    sources_dir = os.path.join(os.path.dirname(__file__), "..", "agents", "fetcher", "sources")
    modules = []
    for f in os.listdir(sources_dir):
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
    """Every fetch() must return a list (stub returns [])."""
    for mod_name in _get_all_fetcher_modules():
        mod = importlib.import_module(f"agents.fetcher.sources.{mod_name}")
        result = mod.fetch()
        assert isinstance(result, list), f"{mod_name}.fetch() returned {type(result)}, expected list"
