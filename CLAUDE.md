# Claude Code Instructions

## Project Objective

Build an automated daily digest system that tracks open-source AI video generation models, specifically for anime/webtoon/visual novel creators. The system aggregates from 30+ sources, stores state in Supabase, and outputs a daily Markdown + HTML digest.

The owner of this project is an anime/webtoon creator interested in:
- Open-source video generation models (Wan2.2, AniSora, HunyuanVideo, etc.)
- Anime-specific LoRAs, ComfyUI workflows, and community tooling
- Interactive fiction tools (Ren'Py, Twine, SillyTavern)
- Copyright/ethics debates around AI training data in anime
- Creator-first perspective (not enterprise/corporate)

## Key Documentation

Read these before implementing anything, **in this order**:

| Doc | Priority | Purpose |
|-----|----------|---------|
| `docs/CONVERSATION_CONTEXT.md` | **READ FIRST** | The user's full needs, interests, and preferences extracted from the design conversations. Understand *who* this is for and *what* they care about before writing any code. |
| `docs/SOURCE_EXPLORATION.md` | **CRITICAL** | Every source researched with exact URLs, APIs, rate limits, auth requirements, and recommended approaches. This is your implementation bible. |
| `docs/ARCHITECTURE.md` | Important | System design, data flow, agent responsibilities |
| `docs/SCHEMA.md` | Important | Supabase table definitions — create these tables first |
| `docs/AGENTS.md` | Important | Contracts and interfaces each agent must follow |
| `docs/SOURCES.md` | Reference | Machine-readable source registry (to be populated by you) |

## Implementation Priority

Work in this order. Each phase should be functional before moving to the next.

### Phase 1: Foundation
1. **Set up Supabase tables** per `docs/SCHEMA.md`
2. **Implement `shared/config.py`** — load env vars, source definitions
3. **Implement `shared/supabase_client.py`** — Supabase connection wrapper
4. **Implement `shared/translator.py`** — deep-translator wrapper with caching
5. **Write basic tests** to verify Supabase connection and translator work

### Phase 2: Fetcher Agent (the core)
Implement fetchers in this order (most reliable first):

**Tier 1 — RSS/Atom feeds (always work, no auth):**
6. `agents/fetcher/sources/github_releases.py` — 8 repo Atom feeds
7. `agents/fetcher/sources/huggingface.py` — 2 RSS feeds (papers + trending)
8. `agents/fetcher/sources/arxiv.py` — cs.CV RSS with keyword filter
9. `agents/fetcher/sources/anime_news.py` — ANN RSS
10. `agents/fetcher/sources/youtube_rss.py` — 7 channel RSS feeds
11. `agents/fetcher/sources/reddit_rss.py` — 5 subreddit RSS feeds
12. `agents/fetcher/sources/itchio.py` — itch.io RSS

**Tier 2 — APIs (need keys or have rate limits):**
13. `agents/fetcher/sources/civitai.py` — CivitAI REST API (no auth needed)
14. `agents/fetcher/sources/comfyui_nodes.py` — ComfyUI Manager node list diff
15. `agents/fetcher/sources/sakugabooru.py` — Booru JSON API

**Tier 3 — RSSHub-dependent (Chinese sources):**
16. `agents/fetcher/sources/bilibili.py` — via RSSHub
17. `agents/fetcher/sources/chinese_ai_news.py` — 36kr/机器之心 via RSSHub

**Tier 4 — Web scrapers (most fragile):**
18. `agents/fetcher/sources/anime_corner.py` — WordPress scrape
19. `agents/fetcher/sources/gigazine.py` — RSS (already available, just add JP keyword filter)
20. `agents/fetcher/sources/legal_policy.py` — CODA/METI (weekly only)
21. `agents/fetcher/sources/pixiv.py` — via RSSHub
22. `agents/fetcher/sources/clip_studio.py` — scrape (weekly)
23. `agents/fetcher/sources/lemmasoft.py` — forum scrape (weekly)

24. **Implement `agents/fetcher/main.py`** — orchestrates all fetchers, handles failures gracefully

### Phase 3: Scorer Agent
25. **Implement `agents/scorer/main.py`** — reads items from Supabase, applies scoring:
    - Recency score (newer = higher)
    - Engagement score (stars, downloads, upvotes — normalized)
    - Keyword relevance boost (anime/webtoon/visual novel terms)
    - Source priority weighting

### Phase 4: Renderer Agent
26. **Implement `agents/renderer/main.py`** — reads scored items, generates:
    - `outputs/YYYY-MM-DD.md` — daily Markdown digest
    - `outputs/YYYY-MM-DD.html` — mobile-friendly HTML (use template in `templates/`)
    - Organized by category (Models, Industry, Community, YouTube, Legal)

### Phase 5: Orchestration
27. **Implement `run.py`** — runs fetcher → scorer → renderer sequentially
28. **Implement `.github/workflows/daily-digest.yml`** — cron schedule (daily)
29. **Implement `.github/workflows/manual-trigger.yml`** — manual dispatch

### Phase 6: Enrichment (optional)
30. GitHub API enrichment (star velocity)
31. YouTube Data API enrichment (view counts)
32. Reddit PRAW for engagement metrics

## Technical Decisions (You Decide)

The following are left to your judgment. Pick the best approach:

- **RSS parsing library**: `feedparser` is suggested but use whatever works best
- **HTML scraping approach**: `beautifulsoup4` + `requests` is suggested, but `httpx` or `selectolax` are fine too
- **Error handling patterns**: Design retry logic, backoff, and failure logging as you see fit
- **Scoring algorithm details**: The doc describes weighted scoring — design the exact weights and normalization
- **HTML template design**: Make it mobile-friendly and clean. The user reads this on their phone.
- **Deduplication strategy**: Content hash is suggested (SHA-256 of source_id + url + title) but adapt as needed
- **Code organization**: The stub structure is a suggestion. Reorganize if it makes more sense.

## Environment Variables

These will be provided via `.env` or GitHub Action secrets:

```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...  (service role key)
SUPABASE_ANON_KEY=eyJ...  (anon key, for RLS if needed)

# Optional
GITHUB_TOKEN=ghp_...  (for API enrichment, higher rate limits)
YOUTUBE_API_KEY=AIza...  (for view count enrichment)
RSSHUB_URL=https://your-rsshub-instance.com  (self-hosted RSSHub)
```

## Coding Conventions

- Python 3.11+
- Type hints on all function signatures
- Docstrings on all public functions
- Each fetcher is a standalone module that can be tested independently
- All timestamps in UTC ISO 8601
- Logging via Python's `logging` module (not print statements)
- Every fetcher must handle failures gracefully — return empty list, never crash the pipeline

## Testing

- Test each fetcher independently: `python -m pytest tests/test_fetcher_github.py`
- Test with mock data where possible (don't hit real APIs in CI)
- Integration test: run full pipeline against Supabase staging

## What NOT To Do

- Don't over-engineer. This runs once a day. Performance doesn't matter.
- Don't add a web framework (Flask/FastAPI). This is a batch job.
- Don't use async unless a specific source benefits from it (Bilibili API is async, most others aren't).
- Don't implement Discord/Slack notifications yet — that's a future phase.
- Don't add a database migration tool — Supabase schema is managed via SQL in `docs/SCHEMA.md`.
