# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                   GitHub Actions (Cron)                   │
│                   runs daily at ~08:00 UTC                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    run.py (orchestrator)                  │
│         fetcher → scorer → renderer (sequential)         │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ FETCHER  │  │  SCORER  │  │ RENDERER │
  │  AGENT   │  │  AGENT   │  │  AGENT   │
  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │              │              │
       ▼              ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                      SUPABASE                            │
│                                                          │
│  items ──── scores ──── digest_runs ──── translations    │
│                                                          │
│  sources_config (source definitions + health tracking)   │
└─────────────────────────────────────────────────────────┘
```

## Agent Responsibilities

### Fetcher Agent (`agents/fetcher/`)
- Pulls data from all sources (RSS, APIs, scrapers)
- Deduplicates against existing items in Supabase (by content_hash)
- Translates CJK content via `shared/translator.py`
- Writes new items to `items` table
- Logs run metadata to `digest_runs` table
- **Must handle failures gracefully** — a single source failure must not crash the pipeline

### Scorer Agent (`agents/scorer/`)
- Reads unscored items from current run
- Applies weighted scoring:
  - **Recency**: Items from last 24h score highest
  - **Engagement**: Stars, downloads, upvotes (normalized per source)
  - **Keyword relevance**: Boost for anime/webtoon/visual novel terms
  - **Source priority**: GitHub releases > Community > Industry > Legal
- Writes scores to `scores` table

### Renderer Agent (`agents/renderer/`)
- Reads top-scored items for the day
- Groups by category (Models, Industry, Community, YouTube, Legal)
- Generates Markdown digest (`outputs/YYYY-MM-DD.md`)
- Generates mobile-friendly HTML (`outputs/YYYY-MM-DD.html`)
- Commits output files to repo (in GitHub Actions context)

### Summarizer Agent (`agents/summarizer/`) — FUTURE / Phase 2
- Claude API-powered summarization of fetched items
- Generates concise 2-3 sentence summaries per item
- Identifies cross-cutting themes across sources
- Not part of initial implementation

## Data Flow

1. **Fetch**: Each source fetcher produces a list of `FetchItem` dicts
2. **Dedup**: Items are hashed (SHA-256 of source_id + url + title) and checked against Supabase
3. **Translate**: Non-English items get translated, originals preserved
4. **Store**: New items written to Supabase `items` table
5. **Score**: Scorer reads today's items, computes weighted scores
6. **Render**: Renderer reads top items, generates output files
7. **Commit**: GitHub Action commits new output files to repo

## Shared Modules (`shared/`)

| Module | Purpose |
|--------|---------|
| `config.py` | Environment variables, source definitions, keyword lists |
| `supabase_client.py` | Supabase connection wrapper, CRUD helpers |
| `translator.py` | deep-translator wrapper with Supabase caching |
| `models.py` | Data classes / TypedDicts for FetchItem, Score, etc. |
| `utils.py` | Hashing, date parsing, text cleaning utilities |

## Failure Modes

| Failure | Behavior |
|---------|----------|
| Single source fetch fails | Log error, skip source, continue pipeline |
| Supabase connection fails | Retry 3x with backoff, then abort run |
| Translation fails | Use original text, mark as untranslated |
| All sources fail | Generate empty digest with error notice |
| GitHub Actions timeout | 6hr max; pipeline should complete in <10min |

## Configuration

All configuration lives in `shared/config.py` and is driven by:
1. Environment variables (`.env` for local, GitHub Secrets for Actions)
2. Source definitions (hardcoded in config, or loaded from Supabase `sources_config`)
3. Keyword lists for filtering and scoring
