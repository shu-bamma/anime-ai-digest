"""
Summarizer Agent — generates per-item summaries, themes, editor's pick, and editorial highlights.

Uses Azure OpenAI to transform raw items into a curated mid-week bulletin.
"""
import json
import logging
from datetime import datetime, timezone

from shared import config, supabase_client
from shared.llm_client import generate
from shared.utils import truncate, clean_html

logger = logging.getLogger(__name__)

BATCH_SIZE = 10
BODY_TRUNCATE_LEN = 300


def _prepare_item(item: dict) -> dict:
    """Extract fields needed for summarization."""
    title = item.get("title_translated") or item.get("title", "")
    body = item.get("body_translated") or item.get("raw_body", "")
    body = truncate(clean_html(body), BODY_TRUNCATE_LEN) if body else ""
    return {
        "id": item.get("id", ""),
        "title": title,
        "body": body,
        "source_id": item.get("source_id", ""),
        "source_category": item.get("source_category", ""),
        "url": item.get("url", ""),
    }


def _summarize_batch(items: list[dict]) -> list[dict]:
    """Summarize a batch of items. Returns list of {id, summary, tldr}."""
    items_text = json.dumps(
        [{"id": i["id"], "title": i["title"], "body": i["body"], "source_id": i["source_id"]}
         for i in items],
        ensure_ascii=False,
    )
    prompt = f"""You are writing for "The Anime AI Digest" — a mid-week bulletin for anime and webtoon creators who use AI tools in their workflow.

For each item below, write:
- "summary": 2 sentences in an objective, informative tone (knowledgeable but neutral — never corporate, never prescriptive). Sentence 1 = what this is, concretely. Sentence 2 = the broader significance or what's notable about it. Max 60 words.
- "tldr": A punchy 5-8 word hook that makes someone want to read more.

Rules:
- Never say "this article discusses" or "this paper presents"
- If it's a LoRA, say what style/subject it targets and its notable characteristics
- If it's a model release, name the key capability improvement
- If it's a tutorial, say what workflow it covers
- Be specific about tools: name them (ComfyUI, Wan2, Clip Studio, etc.)
- Be objective. Do not tell the reader what to do. Report facts, not recommendations.

Items:
{items_text}

Return JSON: {{"summaries": [{{"id": "...", "summary": "...", "tldr": "..."}}]}}"""

    response = generate(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    try:
        parsed = json.loads(response)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for key in ("summaries", "items", "results"):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key]
            if "id" in parsed and "summary" in parsed:
                return [parsed]
        logger.warning(f"Unexpected summary response format: {type(parsed)}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse summary response: {e}")
        return []


def _extract_themes(items_with_summaries: list[dict]) -> list[str]:
    """Extract 3-5 cross-cutting themes from all items."""
    items_text = json.dumps(
        [{"title": i["title"], "summary": i.get("summary", "")} for i in items_with_summaries],
        ensure_ascii=False,
    )
    prompt = f"""You are curating the weekly section headers for "The Anime AI Digest".

Given these items, write 3-5 theme phrases that are OBJECTIVE and SPECIFIC — they describe what happened this period as factual news headlines, not instructions or suggestions.

Good examples: "Wan2 LoRA ecosystem expands with character consistency focus", "ComfyUI nodes for animation loops gain traction", "New open-source video models target anime aesthetics"
Bad examples: "Try new Wan2 LoRAs", "Use ComfyUI nodes for animation", "Start blending these tools", "Bridging illustration and motion design", "Community-driven innovation"

NEVER use imperative voice. NEVER tell the reader what to do. Report trends and developments as an observer.

Items:
{items_text}

Return JSON: {{"themes": ["...", "..."]}}"""

    response = generate(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.4,
        response_format={"type": "json_object"},
    )

    try:
        parsed = json.loads(response)
        if isinstance(parsed, dict) and "themes" in parsed:
            return parsed["themes"]
        if isinstance(parsed, list):
            return parsed
        return []
    except json.JSONDecodeError:
        logger.error("Failed to parse themes response")
        return []


def _generate_highlights(themes: list[str], top_items: list[dict]) -> str:
    """Generate 3 paragraph editorial for the bulletin opening."""
    items_text = json.dumps(
        [{"title": i["title"], "summary": i.get("summary", ""), "source_id": i.get("source_id", "")}
         for i in top_items[:10]],
        ensure_ascii=False,
    )
    themes_text = ", ".join(themes)
    days = config.DIGEST_WINDOW_HOURS // 24
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    prompt = f"""You are writing the opening section of "The Anime AI Digest" — a mid-week bulletin covering AI tools for anime/webtoon/visual novel creation.

Write 3 SHORT paragraphs (2-3 sentences each):
1. The biggest development this period — what happened and who released it? State the facts.
2. Community activity — what tools, workflows, or LoRAs are trending? Report factual observations about adoption and usage.
3. Broader context — how does this fit into the current landscape of AI-assisted anime/webtoon creation? Note the significance without prescribing action.

Voice: Objective news reporting with domain expertise. Reference specific tools by name. No corporate speak.

CRITICAL RULES:
- NEVER use imperative voice ("try", "start", "plug in", "check out", "explore").
- NEVER tell the reader what to do or what their "next step" is.
- NEVER use "you" or "your workflow".
- Report facts, trends, and significance — not recommendations.

Date: {date_str} (covering the past {days} days)
Themes: {themes_text}

Top items:
{items_text}

Write only the paragraphs. No markdown headings, no bullet lists, no fences."""

    return generate(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.5,
    )


def _select_editors_pick(items_with_summaries: list[dict]) -> dict | None:
    """Select one item as the editor's pick with a short callout reason."""
    items_text = json.dumps(
        [{"id": i["id"], "title": i["title"], "summary": i.get("summary", ""),
          "source_id": i.get("source_id", "")}
         for i in items_with_summaries[:20]],
        ensure_ascii=False,
    )
    prompt = f"""From these items in this week's anime AI digest, pick ONE as "Editor's Pick".

Choose the item most immediately useful or exciting for an anime/webtoon creator.
Write a 1-sentence reason (15-25 words) explaining WHY in practical creator terms.

Items:
{items_text}

Return JSON: {{"pick_id": "...", "pick_reason": "..."}}"""

    response = generate(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=256,
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    try:
        parsed = json.loads(response)
        if isinstance(parsed, dict) and "pick_id" in parsed:
            return parsed
        return None
    except json.JSONDecodeError:
        logger.error("Failed to parse editor's pick response")
        return None


def _generate_section_stats(items_by_category: dict[str, list[dict]]) -> dict[str, list[str]]:
    """Generate 3-4 punchy numerical facts per category section."""
    section_stats: dict[str, list[str]] = {}
    for category, items in items_by_category.items():
        if not items:
            continue
        items_text = json.dumps(
            [{"title": i["title"], "summary": i.get("summary", ""), "source_id": i.get("source_id", "")}
             for i in items[:15]],
            ensure_ascii=False,
        )
        prompt = f"""Given these {category} articles from an anime/webtoon AI digest, generate exactly 3-4 punchy numerical/statistical facts.

Examples of good facts:
- "4 new LoRA models released this week"
- "$2.3B anime AI market projected by 2027"
- "12,000+ ComfyUI workflow downloads"
- "3 major video generation models updated"

Each fact must reference a specific number from the articles or a publicly known statistic relevant to the topic.
Keep each fact under 15 words. Be specific, not vague.

Articles:
{items_text}

Return JSON: {{"facts": ["...", "...", "..."]}}"""

        try:
            response = generate(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(response)
            facts = parsed.get("facts", []) if isinstance(parsed, dict) else []
            if facts:
                section_stats[category] = facts[:4]
                logger.info(f"Generated {len(facts[:4])} stats for {category}")
        except Exception as e:
            logger.warning(f"Failed to generate stats for {category}: {e}")
    return section_stats


def run_summarizer(run_id: str) -> dict:
    """Run the summarizer agent. Returns dict with themes, highlights, pick, and count."""
    if not config.AZURE_OPENAI_API_KEY or not config.AZURE_OPENAI_ENDPOINT:
        logger.warning("Azure OpenAI not configured — skipping summarization")
        return {"items_summarized": 0, "themes": [], "highlights": "",
                "tldr_map": {}, "editor_pick_id": None, "editor_pick_reason": "",
                "section_stats": {}}

    # Get top scored items with category diversity
    from agents.scorer.main import apply_source_cap
    scored_items = supabase_client.get_top_scored_items(run_id, limit=1000)
    scored_items = apply_source_cap(scored_items)
    if not scored_items:
        logger.warning("No scored items found for summarization")
        return {"items_summarized": 0, "themes": [], "highlights": "",
                "tldr_map": {}, "editor_pick_id": None, "editor_pick_reason": "",
                "section_stats": {}}

    # Cap to 50 for summarization after diversity selection
    scored_items = scored_items[:50]

    # Extract item data from score rows
    items = []
    for score_row in scored_items:
        item = score_row.get("items", score_row)
        items.append(_prepare_item(item))

    logger.info(f"Summarizing {len(items)} items in batches of {BATCH_SIZE}")

    # Step 1: Per-item summaries in batches
    all_summaries = []
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        try:
            batch_summaries = _summarize_batch(batch)
            all_summaries.extend(batch_summaries)
            logger.info(f"Batch {i // BATCH_SIZE + 1}: summarized {len(batch_summaries)} items")
        except Exception as e:
            logger.error(f"Batch {i // BATCH_SIZE + 1} failed: {e}")

    # Build lookup maps and attach to items
    summary_map = {s["id"]: s["summary"] for s in all_summaries if "id" in s and "summary" in s}
    tldr_map = {s["id"]: s.get("tldr", "") for s in all_summaries if "id" in s}
    for item in items:
        item["summary"] = summary_map.get(item["id"], "")

    # Store summaries in Supabase
    summary_rows = [
        {"item_id": item["id"], "run_id": run_id, "summary": item["summary"]}
        for item in items if item["summary"]
    ]
    if summary_rows:
        try:
            count = supabase_client.insert_summaries(summary_rows)
            logger.info(f"Stored {count} summaries in Supabase")
        except Exception as e:
            logger.error(f"Failed to store summaries: {e}")

    # Step 2: Theme extraction
    try:
        themes = _extract_themes(items)
        logger.info(f"Extracted themes: {themes}")
    except Exception as e:
        logger.error(f"Theme extraction failed: {e}")
        themes = []

    # Step 3: Editorial highlights
    try:
        highlights = _generate_highlights(themes, items)
        logger.info(f"Generated highlights ({len(highlights)} chars)")
    except Exception as e:
        logger.error(f"Highlights generation failed: {e}")
        highlights = ""

    # Step 4: Editor's pick
    editor_pick_id = None
    editor_pick_reason = ""
    try:
        pick = _select_editors_pick(items)
        if pick:
            editor_pick_id = pick.get("pick_id")
            editor_pick_reason = pick.get("pick_reason", "")
            logger.info(f"Editor's pick: {editor_pick_id}")
    except Exception as e:
        logger.error(f"Editor's pick selection failed: {e}")

    # Step 5: Section stats (numerical facts per category)
    section_stats: dict[str, list[str]] = {}
    try:
        items_by_category: dict[str, list[dict]] = {}
        for item in items:
            cat = item.get("source_category", "community")
            items_by_category.setdefault(cat, []).append(item)
        section_stats = _generate_section_stats(items_by_category)
        logger.info(f"Generated section stats for {len(section_stats)} categories")
    except Exception as e:
        logger.error(f"Section stats generation failed: {e}")

    return {
        "items_summarized": len(summary_map),
        "themes": themes,
        "highlights": highlights,
        "tldr_map": tldr_map,
        "editor_pick_id": editor_pick_id,
        "editor_pick_reason": editor_pick_reason,
        "section_stats": section_stats,
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not run_id:
        logger.error("Usage: python -m agents.summarizer.main <run_id>")
        sys.exit(1)
    result = run_summarizer(run_id)
    logger.info(f"Summarizer complete: {result}")
