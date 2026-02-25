# Source Exploration Report
## Anime/Webtoon AI Video Generation Daily Digest

> **Purpose**: This document records the technical exploration of every data source before committing to implementation approaches. It is designed to be consumed by both human developers and AI agents building fetcher modules.
>
> **Date**: 2026-02-26
> **Status**: Pre-implementation research

---

## Table of Contents

1. [Source Categories Overview](#source-categories-overview)
2. [Model Tracking Sources](#1-model-tracking-sources)
3. [Industry News Sources](#2-industry-news-sources)
4. [Community Sources](#3-community-sources)
5. [YouTube Creator Sources](#4-youtube-creator-sources)
6. [Legal & Policy Sources](#5-legal--policy-sources)
7. [Translation Strategy](#translation-strategy)
8. [Rate Limit Budget](#rate-limit-budget)
9. [Recommended Fetch Order](#recommended-fetch-order)
10. [Risk Assessment](#risk-assessment)

---

## Source Categories Overview

| Category | Source Count | Primary Method | Auth Required |
|----------|------------|----------------|---------------|
| Model Tracking | 8 repos + 3 feeds | Atom feeds + RSS | No (Atom), Optional (GitHub API) |
| Industry News | 5 sites | RSS + Scraping | No |
| Community | 10+ platforms | API + RSS + Scraping | Mixed |
| YouTube Creators | 7 channels | YouTube Data API | Yes (API key) |
| Legal/Policy | 2 orgs | Scraping (low freq) | No |

---

## 1. Model Tracking Sources

### 1a. GitHub Releases (8 repositories)

**Repositories to track:**

| Repo | Owner | What to Watch |
|------|-------|---------------|
| Wan-Video | Wan-AI | Wan 2.x releases (MoE architecture, T2V/I2V) |
| Index-AniSora | bilibili | Anime-specific model releases (V3.x) |
| Open-Sora | hpcaitech | Open-Sora 2.x releases |
| HunyuanVideo | Tencent | HunyuanVideo releases, I2V variants |
| CogVideo | THUDM | CogVideoX releases |
| LTX-Video | Lightricks | LTX-Video speed-optimized releases |
| AnimateDiff | guoyww | AnimateDiff + Lightning variants |
| SkyReels-V1 | SkyworkAI | SkyReels human-centric model |

**Recommended Approach: Atom Feeds (PRIMARY) + GitHub API (ENRICHMENT)**

**Atom Feeds (No auth, no rate limit concerns):**
```
https://github.com/{owner}/{repo}/releases.atom
```
- Free, no authentication required
- Returns last ~10 releases with titles, dates, and release notes (HTML content)
- Parse with `feedparser` Python library
- **Limitation**: No star count, fork count, or download metrics in feed
- **Limitation**: Includes pre-releases (no filter parameter available)

**GitHub REST API (For enrichment data):**
```
GET /repos/{owner}/{repo}/releases
GET /repos/{owner}/{repo}  (for star count, fork count)
```
- **Unauthenticated**: 60 requests/hour per IP
- **Authenticated (PAT)**: 5,000 requests/hour
- **GitHub Actions GITHUB_TOKEN**: 1,000 requests/hour per repo
- For 8 repos: ~16 API calls per run (releases + repo stats) — well within any limit
- **Recommendation**: Use authenticated requests via `GITHUB_TOKEN` in Actions, store PAT as secret for local dev

**Data to extract per release:**
- Tag name, release title, published date
- Release body (markdown — contains changelogs, benchmarks)
- Is pre-release? (boolean)
- Author
- Star count delta (compare with previous run via Supabase)

**Implementation notes:**
- Atom feed as primary fetcher (always succeeds, no auth)
- GitHub API as optional enrichment pass (star velocity, download counts)
- Also track `/commits.atom` for repos that don't use formal releases (some push tags only)

---

### 1b. HuggingFace Daily Papers

**RSS Feed (Primary):**
```
https://papers.takara.ai/api/feed
```
- Community-maintained RSS feed of HuggingFace daily papers
- No auth required
- Parse with `feedparser`
- Filter by keywords: `video`, `diffusion`, `anime`, `generation`, `motion`, `temporal`

**HuggingFace Trending Models Feed:**
```
https://zernel.github.io/huggingface-trending-feed/feed.xml
```
- Community-maintained feed of trending models
- No auth required
- Filter by keywords: `wan`, `video`, `anime`, `i2v`, `t2v`, `lora`

**HuggingFace API (Optional enrichment):**
```
GET https://huggingface.co/api/models?sort=trending&filter=video-generation
```
- No auth required for public models
- Rate limit: undocumented but generous (~reasonable for daily checks)
- Returns download count, likes, last modified date

**Recommendation**: RSS feeds as primary, HF API for trending model metrics

---

### 1c. ArXiv cs.CV

**RSS Feed:**
```
https://rss.arxiv.org/rss/cs.CV
```
- Official ArXiv RSS
- No auth
- **Warning**: Very high volume (~100+ papers/day in cs.CV)
- Must aggressively filter by keywords: `video generation`, `anime`, `diffusion video`, `temporal consistency`, `character animation`, `style transfer video`
- Also check `cs.AI` and `cs.MM` (multimedia) for cross-listed papers

**ArXiv API (For enrichment):**
```
GET http://export.arxiv.org/api/query?search_query=...
```
- Free, no auth
- Rate limit: 1 request every 3 seconds
- Useful for full abstract search when RSS title isn't descriptive enough

**Recommendation**: RSS + keyword filter. ArXiv API only for fetching full abstracts of matched papers.

---

## 2. Industry News Sources

### 2a. Anime News Network (ANN)

**RSS Feed:**
```
https://www.animenewsnetwork.com/all/rss.xml?ann-hierarchical
```
- Official RSS, no auth
- Full feed with categories
- Filter for: AI, technology, production, studio news
- **Quality**: High — ANN is the English-language authority on anime industry news
- Keyword filter: `AI`, `artificial intelligence`, `automation`, `technology`, `production`

**Recommendation**: RSS feed with keyword filtering. High signal-to-noise for studio AI adoption stories.

---

### 2b. Anime Corner

**No official RSS detected.**

**Approach**: Web scraping of news page
```
https://animecorner.me/category/news/
```
- Standard WordPress site, clean HTML structure
- Scrape with `requests` + `beautifulsoup4`
- Extract: title, date, URL, excerpt
- Keyword filter same as ANN
- **Risk**: Layout changes may break scraper (WordPress theme updates)
- **Frequency**: Check once daily

**Recommendation**: BeautifulSoup scraper with CSS selector-based extraction. Relatively stable WordPress structure.

---

### 2c. GIGAZINE (Japanese)

**RSS Feed:**
```
https://gigazine.net/news/rss_2.0/
```
- Official RSS, no auth
- **Language**: Japanese — requires translation
- Very high volume tech news site
- Keyword filter (JP): `AI`, `アニメ`, `動画生成`, `人工知能`, `ビデオ`, `画像生成`
- Also filter English loanwords that appear in JP tech: `Wan`, `ComfyUI`, `Stable Diffusion`

**Recommendation**: RSS + bilingual keyword filter (JP + EN terms). Translate matched titles with deep-translator.

---

### 2d. Bilibili AI Channels (B站)

**This is the most technically complex source.**

**Bilibili has no official public API for search/feed.**

**Options explored:**

1. **bilibili-api Python package** (`pip install bilibili-api`)
   - Unofficial, wraps internal Bilibili APIs
   - Requires session cookies for full access (sessdata, bili_jct, buvid3)
   - Can search by keyword, get video metadata
   - **Risk**: Breaks frequently when Bilibili changes internal APIs
   - **Risk**: Cookie-based auth may expire, require manual refresh

2. **bilibili-API-collect** (GitHub: SocialSisterYi/bilibili-API-collect)
   - 16k+ stars — comprehensive documentation of Bilibili's internal APIs
   - Search endpoint: `https://api.bilibili.com/x/web-interface/search/all/v2?keyword=AI动画`
   - Video details: `https://api.bilibili.com/x/web-interface/view?bvid=...`
   - **No official rate limit docs** — community consensus: ~30 requests/minute safe

3. **Direct URL + .json pattern** (like Reddit)
   - Does NOT work for Bilibili — they use server-rendered pages

4. **RSS Bridge / RSSHub** (self-hosted RSS generator)
   - RSSHub has Bilibili routes: `https://rsshub.app/bilibili/search/keyword/AI动画`
   - Can self-host RSSHub in Docker or use public instances
   - **Recommendation**: This is the cleanest approach

**Search keywords for Bilibili:**
- `AI动画` (AI animation)
- `AI视频生成` (AI video generation)
- `Wan2` / `Wan模型`
- `开源视频模型` (open source video model)
- `AniSora`
- `ComfyUI动画`

**Recommendation**: 
- **Phase 1**: Use RSSHub Bilibili routes (self-hosted or public instance)
- **Phase 2**: Direct bilibili-api with cookie management if RSSHub is insufficient
- Always preserve original Bilibili URLs for reference
- Translate titles and descriptions with deep-translator

---

### 2e. 36kr / 机器之心 (Chinese AI Industry)

**36kr:**
- No official RSS
- Has API endpoints discoverable via network inspection
- **Alternative**: RSSHub route: `https://rsshub.app/36kr/newsflashes`
- Filter for AI/video keywords

**机器之心 (Synced / Machine Intelligence):**
```
https://rsshub.app/jiqizhixin/daily
```
- Via RSSHub
- High-quality Chinese AI coverage
- Often first to report Chinese model releases

**Recommendation**: Both via RSSHub. Keyword filter + translate.

---

## 3. Community Sources

### 3a. CivitAI Trending (Anime Video LoRAs)

**CivitAI has a public REST API:**
```
GET https://civitai.com/api/v1/models?sort=Newest&types=LORA&tag=anime,wan,video
GET https://civitai.com/api/v1/models?sort=Most Downloaded&period=Day&types=LORA&tag=anime
```

- **Auth**: Optional (API key gives higher limits, but public endpoints work without)
- **Rate limit**: Undocumented but community reports ~60 req/min unauthenticated
- **Returns**: Model name, description, download count, rating, images, tags, creator
- **Pagination**: Cursor-based (use `metadata.nextPage`)
- **Python SDK**: `pip install civitai-api` (PyPI)

**Queries to run daily:**
1. New models with tags: `anime`, `wan`, `video`, `webtoon`, `animation`
2. Trending models (Most Downloaded, period=Day) with same tags
3. New model versions (updates to existing popular LoRAs)

**Data to extract:**
- Model name, creator, download count (24h velocity)
- Tags, base model compatibility (Wan2.2, SD, FLUX)
- Thumbnail URL, description snippet
- CivitAI model URL

**Recommendation**: Direct API calls, no auth needed for read-only. Filter by anime/video tags. Calculate download velocity by comparing with Supabase state.

---

### 3b. ComfyUI New Custom Nodes

**GitHub search approach:**
```
GET https://api.github.com/search/repositories?q=comfyui+created:>2026-02-25&sort=stars
```
- Finds newly created ComfyUI-related repos
- 30 search requests/minute (authenticated)
- **Also track**: ComfyUI Manager's node list (JSON file in their repo)

**ComfyUI Registry:**
```
https://registry.comfy.org/
```
- Official node registry (newer)
- Has API but documentation is limited

**ComfyUI Manager node list:**
```
https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main/custom-node-list.json
```
- JSON file listing all known custom nodes
- Compare with previous run to detect new additions
- No API call needed — just raw file fetch

**Recommendation**: 
- Primary: Compare ComfyUI Manager's `custom-node-list.json` between runs (stored in Supabase)
- Secondary: GitHub search for new ComfyUI repos with video/anime keywords
- Enrichment: Star count, description, last commit date

---

### 3c. Reddit Subreddits

**Subreddits to monitor:**
- r/comfyui
- r/RenPy
- r/SillyTavernAI
- r/WebtoonCanvas
- r/aiRPGofficial

**Reddit API (OAuth required):**
```
GET https://oauth.reddit.com/r/{subreddit}/new?limit=25&t=day
```
- **Requires**: OAuth app registration + client_id + client_secret
- **Free tier**: 60-100 requests/minute (varies by source)
- **PRAW** library handles auth + rate limiting automatically
- `pip install praw`

**Alternative: JSON endpoint (no auth):**
```
GET https://www.reddit.com/r/{subreddit}/new.json?limit=25
```
- Works without OAuth but rate limited to ~10 req/min
- Requires custom User-Agent header
- **Risk**: Reddit increasingly blocks non-OAuth access

**Alternative: RSS feeds:**
```
https://www.reddit.com/r/{subreddit}/new/.rss
```
- No auth required
- Limited metadata (no score, comment count)
- Sufficient for title + URL + timestamp

**Data to extract per post:**
- Title, URL, author, created_utc
- Score (upvotes), comment count (engagement signal)
- Flair (if available)
- Post text/selftext snippet

**Recommendation**:
- **Phase 1**: RSS feeds for basic monitoring (no auth hassle)
- **Phase 2**: PRAW with OAuth for engagement metrics (score, comments)
- 5 subreddits × 25 posts = 125 items to scan, filter by relevance keywords

---

### 3d. Sakugabooru

**Booru-style API:**
```
GET https://www.sakugabooru.com/post.json?tags=ai+animated&limit=20
```
- Standard Booru API (Danbooru-compatible)
- No auth required
- Tags system for filtering
- **Relevant tags**: `ai`, `animated`, `cgi`, potentially `ai_assisted`
- Returns: post ID, source URL, tags, created_at, score

**Recommendation**: Direct JSON API. Check for posts tagged with AI-related tags. Low volume, high signal.

---

### 3e. Pixiv AI Trends

**Pixiv has no public API for external developers (discontinued in 2019).**

**Options:**
1. **pixivpy3** (unofficial Python API wrapper)
   - `pip install pixivpy3`
   - Requires Pixiv account login (refresh token)
   - Can search by tag, get trending illustrations
   - Tags: `AI生成`, `AIイラスト`, `AI動画`, `Wan2`, `AniSora`

2. **RSSHub Pixiv routes:**
   ```
   https://rsshub.app/pixiv/search/AI動画/popular
   ```
   - Via RSSHub, no direct Pixiv auth needed
   - Limited to search results

**Recommendation**: 
- **Phase 1**: RSSHub Pixiv search route (simplest)
- **Phase 2**: pixivpy3 if more granular data needed
- Low priority — Pixiv AI art is more image-focused than video

---

### 3f. Clip Studio Tips

**Direct URL provided by user:**
```
https://tips.clip-studio.com/en-us/articles/9305
```

**Approach**: Scrape the articles section
```
https://tips.clip-studio.com/en-us/
```
- Standard web page, scrapable with BeautifulSoup
- Filter for articles mentioning: AI, animation, webtoon, video
- Low update frequency (weekly at most)

**Recommendation**: Simple scraper, check weekly not daily. Low priority.

---

### 3g. Lemmasoft Visual Novel Forums

**Direct URL provided by user:**
```
https://lemmasoft.renai.us/forums/index.php
```

**Approach**: Forum scraping
- phpBB-based forum
- RSS feeds may be available: `https://lemmasoft.renai.us/forums/feed`
- If no RSS: scrape "New Posts" or specific subforums
- Filter for AI-related threads
- **Low volume**: Check weekly

**Recommendation**: Check for RSS/Atom feed first. If unavailable, scrape new posts page. Weekly frequency.

---

### 3h. itch.io Twine/Interactive Fiction

**URL provided by user:**
```
https://itch.io/games/tag-interactive-fiction/tag-twine
```

**itch.io has an undocumented API and RSS feeds:**
```
https://itch.io/games/tag-interactive-fiction/tag-twine.xml
```
- Adding `.xml` to browse pages returns RSS
- No auth required
- Filter for AI-mentioned games/tools

**itch.io also has a documented API** (requires API key):
```
GET https://itch.io/api/1/{api_key}/my-games
```
- But this is for your own games only, not for browsing

**Recommendation**: RSS feed (`.xml` suffix on browse URLs). Filter by AI keywords. Weekly frequency.

---

## 4. YouTube Creator Sources

### Channels to Track

| Creator | Channel Focus | Upload Frequency |
|---------|--------------|-----------------|
| SECourses (Furkan Gözükara) | Wan2/ComfyUI/SwarmUI deep tutorials | 2-3x/week |
| Corridor Crew | AI anime experiments, industry perspective | 1-2x/week |
| Next Diffusion | Wan2.2 step-by-step, RunPod guides | 2-3x/week |
| Banodoco | Steerable Motion, anime AI workflows | 1-2x/week |
| Digital Creative AI (DCAI) | JP-focused Wan2.2 deep dives | 1x/week |
| Olivio Sarikas | AI art/video tutorials | 1-2x/week |
| The Local Lab AI | AniSora-specific, Patreon tutorials | 1-2x/week |

### YouTube Data API v3

```
GET https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={id}&order=date&maxResults=5
GET https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}
```

- **Auth**: API key required (free, create in Google Cloud Console)
- **Quota**: 10,000 units/day
- **Cost per search**: 100 units
- **Cost per video details**: 1 unit
- 7 channels × 1 search each = 700 units (7% of daily quota)
- Plus video stats: ~35 units (5 videos × 7 channels × 1 unit)
- **Total**: ~735 units/day — well within 10,000 limit

**Alternative: YouTube RSS feeds (No API key needed):**
```
https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}
```
- Returns last 15 videos per channel
- No auth, no rate limit
- **Limitation**: No view count, like count, or comment count
- Sufficient for detecting new uploads

**Channel IDs needed** (to be looked up during implementation):
- SECourses, Corridor Crew, Next Diffusion, Banodoco, DCAI, Olivio Sarikas, The Local Lab AI

**Data to extract per video:**
- Title, published date, video URL
- Thumbnail URL
- View count, like count (from API, not RSS)
- Description snippet (first 200 chars)

**Recommendation**:
- **Primary**: YouTube RSS feeds (zero API cost, always works)
- **Enrichment**: YouTube Data API for view/like counts on new videos (optional, costs quota)
- Store channel IDs in `sources_config` table

---

## 5. Legal & Policy Sources

### 5a. CODA (Content Overseas Distribution Association, Japan)

```
https://www.coda-cjk.jp/en/
```
- English-language page available
- Low update frequency (monthly)
- Scrape news/press release section
- Keywords: `AI`, `training data`, `copyright`, `generative`

### 5b. Japan METI (Ministry of Economy, Trade and Industry)

```
https://www.meti.go.jp/english/
```
- English-language site
- Press releases and policy papers
- Keywords: `AI`, `copyright`, `content`, `creative`, `anime`
- Low frequency (check weekly)

**Recommendation**: Simple scrapers, weekly frequency. These are signal sources not volume sources — even 1 relevant item is high-value for the digest.

---

## Translation Strategy

### Tool: deep-translator

```python
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='auto', target='en')
result = translator.translate("AI動画生成モデル")
# → "AI video generation model"
```

**Characteristics:**
- Free, no API key
- Wraps Google Translate (good quality for CJK → EN)
- Rate limit: ~5 requests/second (unofficial)
- Batch translation supported (list of strings)
- Auto-detects source language

**Translation caching strategy:**
- Store translations in Supabase `translations` table
- Key: hash(original_text + source_lang + target_lang)
- Prevents re-translating same titles across runs
- Estimated daily new translations: ~50-100 strings

**What to translate:**
- Titles (always)
- Descriptions/excerpts (first 500 chars)
- Tag names (for categorization)

**What NOT to translate:**
- URLs (obvious)
- Author/creator names
- Technical terms that are already English (Wan2.2, ComfyUI, LoRA)

**Always preserve original text alongside translation in Supabase.**

---

## Rate Limit Budget

Daily run budget assuming single GitHub Action execution:

| Source | Method | Requests/Run | Rate Limit | Status |
|--------|--------|-------------|------------|--------|
| GitHub Releases (8 repos) | Atom feeds | 8 | Unlimited | ✅ Safe |
| GitHub API enrichment | REST API | 16 | 1,000/hr (GITHUB_TOKEN) | ✅ Safe |
| HuggingFace Papers | RSS | 1 | Unlimited | ✅ Safe |
| HuggingFace Trending | RSS | 1 | Unlimited | ✅ Safe |
| ArXiv cs.CV | RSS | 1 | Unlimited | ✅ Safe |
| Anime News Network | RSS | 1 | Unlimited | ✅ Safe |
| Anime Corner | Scrape | 1 | N/A | ⚠️ Fragile |
| GIGAZINE | RSS | 1 | Unlimited | ✅ Safe |
| Bilibili | RSSHub | 3-5 | RSSHub instance limit | ⚠️ Depends on hosting |
| 36kr / 机器之心 | RSSHub | 2 | RSSHub instance limit | ⚠️ Depends on hosting |
| CivitAI | REST API | 3-5 | ~60/min unauth | ✅ Safe |
| ComfyUI nodes | Raw GitHub file | 1 | Unlimited | ✅ Safe |
| Reddit (5 subs) | RSS | 5 | Unlimited | ✅ Safe |
| Sakugabooru | JSON API | 1 | Undocumented, generous | ✅ Safe |
| Pixiv | RSSHub | 1 | RSSHub instance limit | ⚠️ Depends on hosting |
| Clip Studio | Scrape | 1 | N/A (weekly) | ✅ Safe |
| Lemmasoft | RSS/Scrape | 1 | N/A (weekly) | ✅ Safe |
| itch.io | RSS | 1 | Unlimited | ✅ Safe |
| YouTube (7 channels) | RSS | 7 | Unlimited | ✅ Safe |
| YouTube API enrichment | REST API | ~42 | 10,000 units/day | ✅ Safe |
| CODA | Scrape | 1 | N/A (weekly) | ✅ Safe |
| METI | Scrape | 1 | N/A (weekly) | ✅ Safe |
| deep-translator | Google Translate | ~50-100 | ~5/sec | ✅ Safe |
| **TOTAL** | | **~100-120** | | **All within budget** |

**Conclusion**: The full source list is comfortably achievable in a single GitHub Action run. RSS-first strategy keeps us well under all rate limits.

---

## Recommended Fetch Order

Execute in this order to maximize reliability (most stable first):

### Phase 1: Feeds (instant, reliable)
1. GitHub Atom feeds (8 repos)
2. HuggingFace RSS feeds (2 feeds)
3. ArXiv RSS
4. ANN RSS
5. GIGAZINE RSS
6. Reddit RSS (5 subreddits)
7. YouTube RSS (7 channels)
8. itch.io RSS
9. CivitAI API

### Phase 2: RSSHub-dependent
10. Bilibili (via RSSHub)
11. 36kr / 机器之心 (via RSSHub)
12. Pixiv (via RSSHub)

### Phase 3: Scrapers (most fragile)
13. Anime Corner (scrape)
14. Clip Studio Tips (scrape, weekly)
15. Lemmasoft Forums (scrape, weekly)
16. CODA (scrape, weekly)
17. METI (scrape, weekly)

### Phase 4: Enrichment (optional, uses API quota)
18. GitHub API (star counts, download metrics)
19. YouTube Data API (view counts)
20. ComfyUI Manager node list diff

### Phase 5: Translation
21. Translate all CJK titles/descriptions from Phases 1-3
22. Cache translations in Supabase

---

## Risk Assessment

### High Reliability (>99% uptime)
- GitHub Atom feeds
- ArXiv RSS
- YouTube RSS
- itch.io RSS
- CivitAI API

### Medium Reliability (~90% uptime)
- Reddit RSS (occasionally rate-limited)
- HuggingFace RSS (community-maintained)
- ANN RSS (long-established)
- GIGAZINE RSS (well-maintained)
- Sakugabooru API (small site, occasionally slow)

### Lower Reliability (~80% uptime)
- RSSHub routes (depends on hosting, Bilibili routes break when B站 changes)
- Anime Corner scraper (WordPress theme changes)
- Lemmasoft scraper (phpBB updates)

### Fragile (may need frequent maintenance)
- Bilibili direct API (internal API, changes without notice)
- Pixiv via pixivpy3 (auth token expires, API changes)
- Clip Studio scraper (less predictable site structure)

### Mitigation Strategy
- Every fetcher must have `try/except` with graceful degradation
- Failed fetches logged to Supabase `digest_runs` table with error details
- Digest renders with whatever sources succeeded
- Weekly health check comparing actual vs expected source counts

---

## Key Dependencies

### Python Packages
```
feedparser          # RSS/Atom parsing
requests            # HTTP requests
beautifulsoup4      # HTML scraping
lxml                # XML/HTML parser (faster than html.parser)
deep-translator     # Google Translate wrapper
praw                # Reddit API (Phase 2)
supabase            # Supabase Python client
python-dateutil     # Date parsing across formats
hashlib             # Content dedup hashing (stdlib)
```

### External Services
```
Supabase            # State management, caching, translations
RSSHub              # Self-hosted or public instance for CN sources
GitHub Actions      # Cron execution
Google Cloud        # YouTube Data API key (free tier)
```

### Optional (Phase 2)
```
bilibili-api        # Direct Bilibili access
pixivpy3            # Direct Pixiv access
youtube-transcript-api  # Video transcript extraction
```

---

## RSSHub Deployment Note

Several Chinese sources (Bilibili, 36kr, 机器之心, Pixiv) rely on RSSHub routes. Options:

1. **Public instances** (free but unreliable):
   - `https://rsshub.app/` (rate-limited, sometimes blocked by target sites)
   - Various community mirrors

2. **Self-hosted** (recommended):
   - Docker: `docker run -d -p 1200:1200 diygod/rsshub`
   - Deploy to: Railway, Render, Fly.io (all have free tiers)
   - Or run as a separate GitHub Action service

3. **Vercel deployment** (free, serverless):
   - Fork RSSHub repo, deploy to Vercel
   - Custom domain optional
   - Good for low-volume daily checks

**Recommendation**: Self-host on Render or Railway free tier. Gives reliable access to all Chinese source routes without depending on public instances.

---

## Notes for Agent Consumers

This document is designed to be read by AI agents building fetcher modules. Key conventions:

1. **Each source should be a separate fetcher function** in `agents/fetcher/sources/`
2. **Every fetcher returns a standardized `FetchItem` dict:**
   ```python
   {
       "source_id": "github_wan_video",
       "title": "Wan 2.3 Release",
       "title_translated": "...",  # if non-English
       "original_language": "en",
       "url": "https://github.com/...",
       "content_hash": "sha256:...",
       "raw_body": "...",
       "published_at": "2026-02-26T00:00:00Z",
       "fetched_at": "2026-02-26T08:00:00Z",
       "metadata": {
           "stars": 1234,
           "downloads_24h": 567,
           "score": 89,
           "tags": ["anime", "wan", "lora"]
       }
   }
   ```
3. **Fetcher must handle failures gracefully** — return empty list, never crash the pipeline
4. **All timestamps in UTC ISO 8601**
5. **Content hash is SHA-256 of (source_id + url + title)** for deduplication
