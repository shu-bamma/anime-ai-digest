# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Automated daily digest system for anime/webtoon creators tracking open-source AI video generation models. Aggregates 18+ sources, scores by relevance, summarizes via LLM, renders HTML+Markdown, and emails via Resend. Runs as a daily batch job (not a web server).

Target audience: anime/webtoon/visual novel creators interested in open-source video gen models, LoRAs, ComfyUI workflows, interactive fiction tools, and AI copyright debates.

## Commands

```bash
# Run full pipeline (fetcher → scorer → summarizer → renderer → emailer)
python run.py

# Run tests
python -m pytest tests/

# Run a single test
python -m pytest tests/test_fetchers.py::test_all_fetchers_have_fetch_function

# Install dependencies
pip install -r requirements.txt
```

## Architecture

### Pipeline Flow

```
run.py orchestrates sequentially:
  fetcher → scorer → summarizer → renderer → emailer
```

Each stage reads/writes Supabase. A `run_id` threads through the entire pipeline. If fewer than `MIN_ITEMS_FOR_DIGEST` (3) new items are fetched, the pipeline skips remaining stages.

### Agent Structure

| Agent | Entry Point | Purpose |
|-------|-------------|---------|
| Fetcher | `agents/fetcher/main.py` | Runs 18 source modules, deduplicates, translates CJK, inserts to Supabase |
| Scorer | `agents/scorer/main.py` | Weighted scoring: recency (0.25) + engagement (0.25) + keyword (0.30) + source priority (0.20) |
| Summarizer | `agents/summarizer/main.py` | Azure OpenAI batch summarization, theme extraction, editor's pick, section stats |
| Renderer | `agents/renderer/main.py` | Generates `outputs/YYYY-MM-DD.{md,html}` with category grouping |
| Emailer | `agents/emailer/main.py` | Sends HTML digest via Resend API |

### Shared Modules

| Module | Role |
|--------|------|
| `shared/config.py` | Env vars, source registries (repos/channels/subreddits), keyword lists, scoring weights |
| `shared/models.py` | TypedDicts: `FetchItem`, `ScoreResult`, `DigestRun` |
| `shared/supabase_client.py` | CRUD with retry/backoff for tables: `items`, `scores`, `digest_runs`, `translations`, `summaries` |
| `shared/translator.py` | CJK→English via `deep-translator` with Supabase-backed cache |
| `shared/utils.py` | `content_hash()`, `parse_date()`, `clean_html()`, `detect_language()` |
| `shared/llm_client.py` | Azure OpenAI wrapper with exponential backoff and jitter |

### Fetcher Pattern

Every fetcher in `agents/fetcher/sources/*.py` exports a single `fetch() -> list[dict]` function. Each must:
- Return a list of `FetchItem`-shaped dicts (never raise exceptions)
- Handle its own errors internally (log and return empty list)
- Set `source_category` to one of: `models`, `industry`, `community`, `youtube`, `legal`

Source tiers by reliability: RSS/Atom (Tier 1) → REST APIs (Tier 2) → RSSHub (Tier 3) → Web scrapers (Tier 4).

### Deduplication

`content_hash(source_id, url, title)` → SHA-256. Checked against Supabase `items` table before insert.

### Scoring

Items within a 72-hour window (`DIGEST_WINDOW_HOURS`) are scored. Source cap ensures diversity: minimum 3 items per category, max 8 per individual source.

## Key Documentation

Read in this order before implementing new features:

1. `docs/CONVERSATION_CONTEXT.md` — User needs and preferences
2. `docs/SOURCE_EXPLORATION.md` — Every source with URLs, APIs, rate limits, auth
3. `docs/ARCHITECTURE.md` — System design and data flow
4. `docs/SCHEMA.md` — Supabase table definitions
5. `docs/AGENTS.md` — Agent contracts and interfaces

## Environment Variables

Required: `SUPABASE_URL`, `SUPABASE_KEY`

Optional: `GITHUB_TOKEN`, `YOUTUBE_API_KEY`, `RSSHUB_URL`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_BASE_URL`, `LLM_MODEL`, `RESEND_API_KEY`, `DIGEST_RECIPIENTS`, `DIGEST_FROM_EMAIL`

## Coding Conventions

- Python 3.11+, type hints on all signatures, docstrings on public functions
- Timestamps in UTC ISO 8601
- Logging via `logging` module (not print)
- Fetchers must never crash the pipeline — always return empty list on failure
- No web framework, no async (unless source-specific), no DB migrations tool
- Keyword matching uses word boundaries (`config.keyword_in_text()`) to avoid false positives
