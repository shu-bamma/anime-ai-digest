# LLM-Powered Summarization

## Overview
Add an LLM summarization agent to the anime-ai-digest pipeline that uses Azure OpenAI GPT-5 to generate concise per-item summaries, identify cross-cutting themes across all sources, and produce an editorial "Today's Highlights" section. This transforms the digest from a raw link dump into a curated, readable daily briefing.

## User Stories
- As a reader, I want each item to have a 2-3 sentence summary so I can quickly decide what's worth clicking
- As a reader, I want to see cross-cutting themes so I can understand what's trending across the ecosystem
- As a reader, I want a "Today's Highlights" editorial section at the top so I get the most important takeaways at a glance
- As a pipeline operator, I want summarization to be cost-efficient by batching items and using token-aware chunking

## Data Schema

### New Supabase table: `summaries`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK, default gen_random_uuid() |
| item_id | text | FK to items.item_id |
| run_id | uuid | FK to digest_runs.id |
| summary | text | 2-3 sentence LLM summary |
| created_at | timestamptz | default now() |

### New fields in digest output (not DB — computed at render time)
- `themes`: list of 3-5 cross-cutting theme strings
- `highlights_html`: editorial "Today's Highlights" markdown/HTML block

## Architecture

### New modules
1. **`shared/llm_client.py`** — Azure OpenAI client wrapper (follows roam pattern)
   - Uses `openai.OpenAI(base_url=AZURE_OPENAI_BASE_URL, api_key=AZURE_OPENAI_API_KEY)`
   - Model: `gpt-5-chat` (deployment name from global .env)
   - Retry with exponential backoff on 429/5xx/timeout
   - 120s timeout

2. **`agents/summarizer/main.py`** — Summarizer agent
   - `summarize_items(items, run_id)` → per-item summaries (batched, ~20 items per LLM call)
   - `extract_themes(items_with_summaries)` → list of 3-5 themes
   - `generate_highlights(themes, top_items)` → editorial "Today's Highlights" markdown

### Pipeline integration
Current: `fetcher → scorer → renderer`
New: `fetcher → scorer → summarizer → renderer`

The summarizer receives the top-scored items (same ones the renderer uses) and:
1. Generates per-item summaries in batches
2. Extracts cross-cutting themes from all summaries
3. Generates the "Today's Highlights" editorial
4. Passes enriched data to the renderer

### Renderer changes
- Add "Today's Highlights" section at the top of both MD and HTML output
- Add "Themes" tags/badges below highlights
- Show per-item summaries inline (below the item title, above source/date)

## Edge Cases
- **Azure API rate limits**: Batch items (20 per call) and retry with backoff
- **Token limits**: Truncate item descriptions to ~200 chars before sending to LLM
- **Empty/few items**: Skip themes/highlights if fewer than 5 items scored
- **LLM failure**: Graceful degradation — render digest without summaries if LLM is unavailable
- **Cost control**: Only summarize top 50 items (same as current render limit)
- **Missing Azure credentials**: Skip summarizer entirely, log warning, proceed with unsummarized digest
