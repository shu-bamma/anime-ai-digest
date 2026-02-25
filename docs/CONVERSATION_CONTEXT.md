# Conversation Context for Claude Code

> This document captures the user's needs, preferences, and decisions from the design conversations
> that produced this project. Read this **before** CLAUDE.md to understand the *why* behind the *what*.

---

## Who Is This For?

A technically proficient user who tracks the intersection of **anime/webtoon creation** and **open-source AI video generation models**. They're not an academic researcher — they're a practitioner who cares about what's usable *today* for anime-style video generation, interactive storytelling tools, and community workflows.

They follow this space daily and want an automated digest that saves them from manually checking 30+ sources.

---

## Core Interests (In Their Own Words)

### 1. Open-Source Video Generation Models (Anime/Webtoon Focus)
The user is deeply familiar with the current landscape:
- **Wan2.2** (Alibaba) — MoE architecture, considered the best open-source stack right now
- **Index-AniSora** (Bilibili) — Anime-specialized, 10M+ clips, RLHF-optimized. *Major copyright controversy* (see below)
- **HunyuanVideo** (Tencent) — 13B params, beats Runway Gen-3
- **LTX-Video** (Lightricks) — Lightweight, 12GB VRAM, fast
- **Mochi 1** (Genmo) — 10B params, Apache 2.0
- **CogVideoX** (Tsinghua) — Mid-tier
- **Open-Sora 2.0** — 11B, $200K training, fully open
- **SkyReels** — Human-centric, cinematic focus

They want to know about new releases, LoRA fine-tunes, ComfyUI integrations, benchmark results, and community adoption of these models.

### 2. Copyright & Ethics of Training Data
This is a **high-priority** interest. The Index-AniSora controversy is a key example:
- Bilibili trained on 10M+ clips including Studio Ghibli, Finding Nemo, SpongeBob, Despicable Me, Tangled, Lion King, Angel's Egg — **without disclosed licensing**
- Sony owns 4.98% of Bilibili, yet Sony's Crunchyroll publicly rejected AI in anime
- Japan's CODA is demanding OpenAI and others refrain from using Japanese content for training
- Community reaction was split: technical people were impressed but skeptical; anime fans and artists were overwhelmingly negative, viewing it as betrayal

The digest should surface any news about training data rights, creator pushback, regulatory developments (especially CODA, METI, EU AI Act), and industry position statements.

### 3. Creator & Interactive Storytelling Tools
The user is actively interested in tools for **interactive fiction and visual storytelling**:
- **Ren'Py** — Visual novel engine (r/RenPy)
- **Twine** — Interactive fiction on itch.io
- **SillyTavern** — AI roleplay/chatbot platform (r/SillyTavernAI)
- **Webtoon creation** — Tools, AI-assisted workflows (r/WebtoonCanvas)
- **AI RPG** — Emerging AI-powered RPG tools (r/aiRPGofficial)
- **Lemmasoft Forums** — Visual novel community
- **Clip Studio Tips** — Digital art tutorials for anime/webtoon

These aren't afterthoughts — they're core to what the user reads daily.

### 4. Practical Implementation Over Academic Papers
The user prefers:
- ComfyUI workflows they can run
- LoRAs they can download from CivitAI
- YouTube tutorials showing actual results
- Reddit threads with real user experiences
- NOT pure academic papers (ArXiv is included but heavily filtered)

---

## What They Explicitly Selected

### Sources Selected (from interactive selection process)

**PRIMARY — Model Releases & Research:**
- ✅ GitHub Releases: Wan2.2, AniSora, Open-Sora, HunyuanVideo, CogVideo, LTX-Video, AnimateDiff, SkyReels
- ✅ HuggingFace Daily Papers (video/diffusion filtered)
- ✅ ArXiv cs.CV (aggressive keyword filtering required — high volume)
- ✅ Bilibili AI channels (B站 AI动画 tags, auto-translated)

**COMMUNITY — Workflows, LoRAs, Practitioner Chatter:**
- ✅ CivitAI trending (anime video LoRAs, Wan tags)
- ✅ ComfyUI new custom nodes & workflows
- ✅ Reddit: r/comfyui, r/RenPy, r/SillyTavernAI, r/WebtoonCanvas, r/aiRPGofficial
- ✅ Sakugabooru / Sakuga community (animator reactions)
- ✅ Pixiv AI trends (JP creators experimenting)
- ✅ Clip Studio articles on anime/webtoons
- ✅ Lemmasoft Forums (visual novel community)
- ✅ itch.io interactive fiction (Twine games)

**INDUSTRY & TRACKING:**
- ✅ Anime News Network (studio AI adoption)
- ✅ Anime Corner (industry reactions)
- ✅ GIGAZINE (JP tech, AI anime coverage)
- ✅ YouTube creators (see below)

**LEGAL/POLICY:**
- ✅ CODA / METI (Japanese copyright body)
- ✅ General copyright/ethics tracking

**CHINESE AI NEWS (via RSSHub):**
- ✅ 36kr (Chinese tech news)
- ✅ 机器之心 (Machine Intelligence — CN AI news)

**YOUTUBE CREATORS — Tier 1 (Heavy hitters):**
- ✅ SECourses (Furkan Gözükara) — deep Wan2/ComfyUI/SwarmUI tutorials, 1-click installers
- ✅ Corridor Crew — viral AI anime experiments, industry perspective
- ✅ Next Diffusion — Wan2.2 step-by-step tutorials, RunPod guides
- ✅ Banodoco — Steerable Motion, anime AI video workflows

**YOUTUBE CREATORS — Tier 2 (Supplementary):**
- ✅ Digital Creative AI — JP-focused AI anime content
- ✅ Olivio Sarikas — AI art/video tutorials
- ✅ The Local Lab AI — AniSora-specific coverage

### Explicitly Deferred (Phase 2):
- ❌ Discord server monitoring (Wan2.2, ComfyUI, CivitAI Discords) — "maybe later as phase 2"
- ❌ Claude API summarization agent — Phase 2 after basic pipeline works

### Not Selected / Not Interested:
- Korean webtoon platform APIs (Naver/Kakao/Tappytoon) — mentioned interest but not selected in final source list
- DC Inside (Korean forums) — mentioned but not selected

---

## Key Technical Decisions (User-Made)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| State management | Supabase | User has existing Supabase project, will provide credentials |
| Translation | deep-translator (GoogleTranslator) | Free, no API key needed |
| Ranking approach | All three combined | 24h window + weighted scoring + keyword relevance boost |
| Output format | Markdown + HTML | MD pushed to GitHub repo, HTML for mobile reading |
| Deployment | GitHub Actions (cron) | Self-hosted, daily at 08:00 UTC |
| Summarization | Claude API (Phase 2) | Separate agent, not blocking Phase 1 |
| Non-English content | Auto-translate with original ref links | "ref is a must have" — always link to original |

---

## Digest Priority Order

The user explicitly ranked what they want to see first in each digest:

1. **Anime/webtoon industry AI adoption news** (highest priority)
2. **New model releases & benchmarks**
3. **Community workflows & LoRA drops** (CivitAI, ComfyUI)
4. **Copyright & ethics developments**

---

## Personality & Communication Style

- Casual, fast-paced communicator ("give me boxes to tick for them one by one man")
- Wants exhaustive options presented, then selects from them
- Prefers practical over theoretical
- Wants things to "just work" — robust error handling, graceful degradation
- Values documentation that helps AI agents (Claude Code) implement autonomously
- Thinks in terms of phases — get basics working, then layer complexity

---

## What Success Looks Like

Every morning, the user opens a clean, mobile-friendly digest that tells them:
- What new model versions dropped overnight
- Which anime LoRAs are trending on CivitAI
- What the ComfyUI community built with Wan2.2 this week
- Whether any studio or rights holder made a statement about AI
- What Japanese/Chinese creators are doing with these tools
- Any new Ren'Py/Twine/SillyTavern projects or updates

All non-English content is translated but links to the original. Everything is ranked by relevance to their specific interests. No noise, no academic papers about protein folding that happened to mention "diffusion".
