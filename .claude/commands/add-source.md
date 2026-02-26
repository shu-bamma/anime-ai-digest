Guide me through adding a new source fetcher called $ARGUMENTS.

Follow this checklist:

1. **Create the fetcher module** at `agents/fetcher/sources/$ARGUMENTS.py`
   - Must export `fetch() -> list[dict]`
   - Return FetchItem-shaped dicts with: source_id, source_category, title, url, published_at, raw_body, original_language, metadata
   - Handle all errors internally — log and return empty list, never raise
   - Use `shared.utils.clean_html()` for HTML content, `shared.utils.parse_date()` for dates

2. **Register in fetcher main** — add import and call in `agents/fetcher/main.py`

3. **Add config** if needed — add URLs, keywords, or API keys to `shared/config.py`

4. **Test** — run `/test-fetcher $ARGUMENTS` to verify it works

5. **Run full test suite** — `python -m pytest tests/ -v` to ensure nothing broke

Reference `agents/fetcher/sources/github_releases.py` as the canonical example of the fetcher pattern.
