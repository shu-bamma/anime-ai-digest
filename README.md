# 🎌 Anime AI Video Digest

**Automated daily digest tracking open-source AI video generation models for anime and webtoon creators.**

## What This Is

A Python-based pipeline that runs daily via GitHub Actions. It aggregates news from 30+ sources (GitHub releases, RSS feeds, APIs, web scrapers) about open-source video generation AI — specifically models, LoRAs, workflows, and community developments relevant to anime/webtoon/visual novel creators.

Output: A daily Markdown digest + mobile-friendly HTML, pushed to this repo. State is stored in Supabase.

## Project Status

**🟡 Scaffold only — implementation needed.**

This repo contains the architecture, documentation, source research, and stub files. All implementation is to be done by Claude Code (or a developer) following the docs.

## For Claude Code

**Start here:**
1. Read `CLAUDE.md` — your primary instructions and task list
2. Read `docs/ARCHITECTURE.md` — system design
3. Read `docs/SOURCE_EXPLORATION.md` — every source researched with exact endpoints, rate limits, and recommended approaches
4. Read `docs/SCHEMA.md` — Supabase table designs
5. Read `docs/AGENTS.md` — contracts each agent must follow

Then implement the agents in priority order defined in `CLAUDE.md`.

## Quick Start (after implementation)

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys

# Run the full pipeline locally
python run.py

# Or run agents individually
python -m agents.fetcher.main
python -m agents.scorer.main
python -m agents.renderer.main
```

## Architecture

```
Sources → Fetcher Agent → Supabase → Scorer Agent → Renderer Agent → MD/HTML
                                         ↑
                                   Translation Cache
```

See `docs/ARCHITECTURE.md` for the full design.

## License

MIT
