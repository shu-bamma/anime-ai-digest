# Supabase Schema

## Setup Instructions

Run these SQL statements in the Supabase SQL Editor to create the tables.
Order matters — create tables before their dependents.

## Tables

### `items` — Every fetched content item

```sql
CREATE TABLE items (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,  -- SHA-256 for dedup
    source_id TEXT NOT NULL,            -- e.g. "github_wan_video", "civitai_trending"
    source_category TEXT NOT NULL,      -- "models", "industry", "community", "youtube", "legal"
    
    title TEXT NOT NULL,
    title_translated TEXT,              -- English translation if original is CJK
    original_language TEXT DEFAULT 'en',
    
    url TEXT NOT NULL,
    raw_body TEXT,                      -- Full content (release notes, description, etc.)
    body_translated TEXT,               -- Translated body snippet
    
    published_at TIMESTAMPTZ,           -- When the source published it
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    
    metadata JSONB DEFAULT '{}'::jsonb, -- Flexible: stars, downloads, score, tags, etc.
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_items_source ON items(source_id);
CREATE INDEX idx_items_category ON items(source_category);
CREATE INDEX idx_items_published ON items(published_at DESC);
CREATE INDEX idx_items_fetched ON items(fetched_at DESC);
CREATE INDEX idx_items_hash ON items(content_hash);
```

### `scores` — Computed relevance scores

```sql
CREATE TABLE scores (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES digest_runs(id) ON DELETE CASCADE,
    
    total_score FLOAT NOT NULL DEFAULT 0,
    
    -- Score components (for debugging/tuning)
    recency_score FLOAT DEFAULT 0,
    engagement_score FLOAT DEFAULT 0,
    keyword_score FLOAT DEFAULT 0,
    source_priority_score FLOAT DEFAULT 0,
    
    scored_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scores_item ON scores(item_id);
CREATE INDEX idx_scores_run ON scores(run_id);
CREATE INDEX idx_scores_total ON scores(total_score DESC);
```

### `digest_runs` — Run metadata and health tracking

```sql
CREATE TABLE digest_runs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT DEFAULT 'running',  -- running, completed, failed
    
    items_fetched INT DEFAULT 0,
    items_new INT DEFAULT 0,        -- After dedup
    items_scored INT DEFAULT 0,
    sources_succeeded INT DEFAULT 0,
    sources_failed INT DEFAULT 0,
    
    errors JSONB DEFAULT '[]'::jsonb,  -- Array of {source_id, error, timestamp}
    
    output_md TEXT,     -- Path to generated markdown
    output_html TEXT    -- Path to generated HTML
);

CREATE INDEX idx_runs_status ON digest_runs(status);
CREATE INDEX idx_runs_started ON digest_runs(started_at DESC);
```

### `translations` — Translation cache

```sql
CREATE TABLE translations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    text_hash TEXT NOT NULL,            -- SHA-256 of original text
    original_text TEXT NOT NULL,
    source_language TEXT NOT NULL,
    target_language TEXT DEFAULT 'en',
    translated_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_translations_lookup 
    ON translations(text_hash, source_language, target_language);
```

### `sources_config` — Source definitions and health (optional)

```sql
CREATE TABLE sources_config (
    id TEXT PRIMARY KEY,                -- e.g. "github_wan_video"
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    fetch_method TEXT NOT NULL,         -- "rss", "api", "scrape"
    url TEXT NOT NULL,                  -- Feed URL or API endpoint
    
    enabled BOOLEAN DEFAULT TRUE,
    frequency TEXT DEFAULT 'daily',     -- "daily", "weekly"
    
    last_fetch_at TIMESTAMPTZ,
    last_fetch_status TEXT,             -- "ok", "error"
    consecutive_failures INT DEFAULT 0,
    
    config JSONB DEFAULT '{}'::jsonb,   -- Source-specific config (keywords, auth, etc.)
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Notes

- **RLS (Row Level Security)**: Not needed — this is a backend service using the service role key.
- **Indexes**: Added on frequently queried columns. Adjust based on actual query patterns.
- **JSONB metadata**: Used for flexible per-source data (stars, downloads, tags, etc.) that varies by source type.
- **content_hash**: The primary dedup mechanism. SHA-256 of (source_id + url + title).
- **Create `digest_runs` BEFORE `scores`** — scores has a foreign key to digest_runs.
