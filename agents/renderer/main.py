"""
Renderer Agent — generates mid-week bulletin digest (Markdown + HTML).

Reads top-scored items from Supabase, groups by category, renders a premium
newspaper-style bulletin with categorized sections, stats boxes, and editor's pick.
"""
import logging
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from shared import config, supabase_client
from shared.utils import truncate, clean_html
from agents.scorer.main import apply_source_cap

logger = logging.getLogger(__name__)

REPO_URL = "https://github.com/shu-bamma/anime-ai-digest"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "outputs"

CATEGORIES = [
    ("models", "Model Releases & Updates"),
    ("industry", "Industry News"),
    ("community", "Community & Workflows"),
    ("youtube", "YouTube"),
    ("legal", "Copyright & Legal"),
]

CATEGORY_EMOJI = {
    "models": "\U0001f3ac",       # 🎬
    "industry": "\U0001f4f0",     # 📰
    "community": "\U0001f3a8",    # 🎨
    "youtube": "\U0001f4fa",      # 📺
    "legal": "\u2696\ufe0f",      # ⚖️
}

# Within each category, show this many as full cards; rest as compact links
FULL_CARDS_PER_CATEGORY = 3


def _time_ago(published_at: str | None) -> str:
    if not published_at:
        return ""
    try:
        from shared.utils import parse_date
        dt = parse_date(published_at)
        if not dt:
            return ""
        now = datetime.now(timezone.utc)
        delta = now - dt
        hours = delta.total_seconds() / 3600
        if hours < 1:
            return "just now"
        if hours < 24:
            return f"{int(hours)}h ago"
        days = int(hours / 24)
        return f"{days}d ago"
    except Exception:
        return ""


def _get_item_data(item_data: dict) -> dict:
    """Extract normalized item fields from a score row."""
    item = item_data.get("items", item_data)
    return {
        "id": item.get("id", ""),
        "title": item.get("title_translated") or item.get("title", ""),
        "url": item.get("url", ""),
        "source_id": item.get("source_id", ""),
        "source_category": item.get("source_category", "community"),
        "published_at": item.get("published_at", ""),
        "metadata": item.get("metadata", {}),
        "body": item.get("body_translated") or item.get("raw_body", ""),
    }


def _group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    """Group items by source_category, preserving score order within each group."""
    groups: dict[str, list[dict]] = {}
    for item in items:
        cat = item.get("source_category", "community")
        groups.setdefault(cat, []).append(item)
    return groups


# =============================================================================
# MARKDOWN RENDERER
# =============================================================================

def _render_markdown(date_str: str, all_items: list[dict], summary_data: dict | None = None,
                     item_summaries: dict[str, str] | None = None) -> str:
    lines = [f"# The Anime AI Digest — {date_str}\n"]
    days = config.DIGEST_WINDOW_HOURS // 24
    section_stats = summary_data.get("section_stats", {}) if summary_data else {}

    # Executive brief
    if summary_data and summary_data.get("highlights"):
        lines.append(f"\n## \U0001f31f This Week in Anime AI\n")
        lines.append(summary_data["highlights"])
        lines.append("")

    # Theme tags
    if summary_data and summary_data.get("themes"):
        themes_str = " | ".join(f"**{t}**" for t in summary_data["themes"])
        lines.append(f"\n> {themes_str}\n")

    # Editor's pick
    pick_id = summary_data.get("editor_pick_id") if summary_data else None
    pick_reason = summary_data.get("editor_pick_reason", "") if summary_data else ""
    if pick_id:
        for item in all_items:
            if item["id"] == pick_id:
                lines.append(f"\n### \u2b50 Editor's Pick: [{item['title']}]({item['url']})")
                if pick_reason:
                    lines.append(f"> {pick_reason}")
                lines.append("")
                break

    # Category sections
    tldr_map = summary_data.get("tldr_map", {}) if summary_data else {}
    grouped = _group_by_category(all_items)

    for cat_key, cat_label in CATEGORIES:
        cat_items = grouped.get(cat_key, [])
        if not cat_items:
            continue
        emoji = CATEGORY_EMOJI.get(cat_key, "")
        lines.append(f"\n## {emoji} {cat_label}\n")

        # Section stats
        stats = section_stats.get(cat_key, [])
        if stats:
            for stat in stats:
                lines.append(f"- \U0001f4ca {stat}")
            lines.append("")

        for idx, item in enumerate(cat_items, 1):
            tldr = tldr_map.get(item["id"], "")
            summary = item_summaries.get(item["id"], "") if item_summaries else ""
            ago = _time_ago(item["published_at"])
            meta_parts = [item["source_id"]]
            if ago:
                meta_parts.append(ago)

            if idx <= FULL_CARDS_PER_CATEGORY:
                if not summary:
                    summary = truncate(clean_html(item["body"]), 150) if item["body"] else ""
                lines.append(f"**{idx}. {tldr or item['title']}**")
                lines.append(f"[{item['title']}]({item['url']})")
                if summary:
                    lines.append(f"{summary}")
                lines.append(f"*{' · '.join(meta_parts)}*\n")
            else:
                meta = f" — {' · '.join(meta_parts)}"
                lines.append(f"- [{item['title']}]({item['url']}){meta}")

    lines.append(f"\n---\n*The Anime AI Digest • [Source]({REPO_URL})*\n")
    return "\n".join(lines)


# =============================================================================
# HTML BULLETIN RENDERER (email-safe, inline styles)
# =============================================================================

# Color palette
_BG = "#f4f1eb"
_CARD = "#ffffff"
_MASTHEAD = "#1a1a2e"
_MASTHEAD_TEXT = "#f4f1eb"
_ACCENT = "#e63946"
_BODY_TEXT = "#2d2d2d"
_MUTED = "#6b7280"
_BORDER = "#e5e7eb"
_BADGE_BG = "#f3f4f6"
_PICK_BG = "#fef3c7"
_STATS_BG = "#fdf6e3"
_STATS_BORDER = "#f0e6cc"


def _render_stats_box(stats: list[str]) -> str:
    """Render a styled stats box for a category section."""
    if not stats:
        return ""
    bullets = "".join(
        f'<li style="margin:3px 0;font-family:-apple-system,sans-serif;font-size:12px;color:{_BODY_TEXT};line-height:1.5;">'
        f'\U0001f4ca {escape(s)}</li>'
        for s in stats
    )
    return f'''<tr><td style="padding:12px 32px 4px;">
  <div style="background:{_STATS_BG};border:1px solid {_STATS_BORDER};border-radius:6px;padding:10px 14px;">
    <ul style="margin:0;padding-left:16px;list-style:none;">{bullets}</ul>
  </div>
</td></tr>'''


def _render_item_card(item: dict, idx: int, tldr: str, summary: str, pick_id: str | None) -> str:
    """Render a full item card for lead items within a category."""
    ago = _time_ago(item["published_at"])
    source = item["source_id"]
    meta_parts = [f'<span style="color:{_MUTED};font-size:12px;">{escape(source)}</span>']
    if ago:
        meta_parts.append(f'<span style="color:{_MUTED};font-size:12px;">{escape(ago)}</span>')

    num_bg = _ACCENT
    return f'''<tr><td style="padding:14px 32px;border-bottom:1px solid {_BORDER};">
  <table cellpadding="0" cellspacing="0"><tr>
    <td style="vertical-align:top;padding-right:12px;">
      <div style="width:24px;height:24px;border-radius:50%;background:{num_bg};color:#fff;font-family:-apple-system,sans-serif;font-size:12px;font-weight:700;text-align:center;line-height:24px;">{idx}</div>
    </td>
    <td>
      {f'<p style="margin:0 0 2px;font-family:-apple-system,sans-serif;font-size:11px;font-weight:600;color:{_ACCENT};text-transform:uppercase;letter-spacing:0.5px;">{escape(tldr)}</p>' if tldr else ''}
      <a href="{escape(item['url'])}" target="_blank" style="font-family:Georgia,\'Times New Roman\',serif;font-size:15px;font-weight:600;color:{_BODY_TEXT};text-decoration:none;line-height:1.3;">{escape(item['title'])}</a>
      {f'<p style="margin:5px 0 0;font-family:-apple-system,sans-serif;font-size:13px;line-height:1.5;color:{_BODY_TEXT};opacity:0.85;">{escape(summary)}</p>' if summary else ''}
      <p style="margin:6px 0 0;">{"&middot;".join(meta_parts)} &middot; <a href="{escape(item['url'])}" target="_blank" style="color:{_ACCENT};font-size:12px;text-decoration:none;font-family:-apple-system,sans-serif;">Read&nbsp;more&nbsp;&rarr;</a></p>
    </td>
  </tr></table>
</td></tr>'''


def _render_compact_link(item: dict) -> str:
    """Render a compact link for remaining items in a category."""
    ago = _time_ago(item["published_at"])
    source = item["source_id"]
    meta = f'{escape(source)}'
    if ago:
        meta += f' &middot; {escape(ago)}'
    return f'''<tr><td style="padding:6px 32px 6px 68px;border-bottom:1px solid {_BORDER};">
  <a href="{escape(item['url'])}" target="_blank" style="font-family:-apple-system,sans-serif;font-size:13px;color:{_BODY_TEXT};text-decoration:none;font-weight:500;">{escape(item['title'])}</a>
  <span style="font-size:11px;color:{_MUTED};margin-left:6px;">{meta}</span>
</td></tr>'''


def _render_category_section(cat_key: str, cat_label: str, cat_items: list[dict],
                              tldr_map: dict, item_summaries: dict, section_stats: dict,
                              pick_id: str | None) -> str:
    """Render a full category section with header, stats, cards, and compact links."""
    emoji = CATEGORY_EMOJI.get(cat_key, "")
    stats = section_stats.get(cat_key, [])
    stats_html = _render_stats_box(stats)

    # Full cards for top items
    cards_html = ""
    for idx, item in enumerate(cat_items[:FULL_CARDS_PER_CATEGORY], 1):
        tldr = tldr_map.get(item["id"], "")
        summary = item_summaries.get(item["id"], "")
        if not summary:
            summary = truncate(clean_html(item["body"]), 120) if item["body"] else ""
        cards_html += _render_item_card(item, idx, tldr, summary, pick_id)

    # Compact links for the rest
    links_html = ""
    for item in cat_items[FULL_CARDS_PER_CATEGORY:]:
        links_html += _render_compact_link(item)

    return f'''<table width="100%" cellpadding="0" cellspacing="0" style="background:{_CARD};border:1px solid {_BORDER};margin-top:2px;">
<tr><td style="padding:18px 32px 6px;">
  <h2 style="margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px;font-weight:700;color:{_BODY_TEXT};text-transform:uppercase;letter-spacing:1px;">{emoji} {escape(cat_label)}</h2>
</td></tr>
{stats_html}
{cards_html}
{links_html}
</table>'''


def _render_bulletin_html(date_str: str, all_items: list[dict],
                          summary_data: dict | None = None,
                          item_summaries: dict[str, str] | None = None) -> str:
    days = config.DIGEST_WINDOW_HOURS // 24
    tldr_map = summary_data.get("tldr_map", {}) if summary_data else {}
    pick_id = summary_data.get("editor_pick_id") if summary_data else None
    pick_reason = summary_data.get("editor_pick_reason", "") if summary_data else ""
    section_stats = summary_data.get("section_stats", {}) if summary_data else {}

    # --- Masthead ---
    masthead = f'''<table width="100%" cellpadding="0" cellspacing="0" style="background:{_MASTHEAD};border-radius:8px 8px 0 0;">
<tr><td style="padding:28px 32px;">
  <h1 style="margin:0;font-family:Georgia,'Times New Roman',serif;font-size:24px;font-weight:700;color:{_MASTHEAD_TEXT};letter-spacing:-0.5px;">The Anime AI Digest</h1>
  <p style="margin:6px 0 0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px;color:{_MASTHEAD_TEXT};opacity:0.7;">{date_str} &middot; Covering the past {days} days</p>
</td></tr></table>'''

    # --- Executive Brief ---
    brief_html = ""
    if summary_data and summary_data.get("highlights"):
        paragraphs = ""
        for para in summary_data["highlights"].strip().split("\n\n"):
            para = para.strip()
            if para:
                paragraphs += f'<p style="margin:0 0 12px;font-family:Georgia,\'Times New Roman\',serif;font-size:15px;line-height:1.7;color:{_BODY_TEXT};">{escape(para)}</p>'

        theme_badges = ""
        if summary_data.get("themes"):
            badges = "".join(
                f'<span style="display:inline-block;background:{_ACCENT};color:#fff;font-size:11px;font-weight:600;padding:3px 10px;border-radius:12px;margin:2px 4px 2px 0;font-family:-apple-system,sans-serif;">{escape(t)}</span>'
                for t in summary_data["themes"]
            )
            theme_badges = f'<div style="margin-top:14px;">{badges}</div>'

        brief_html = f'''<table width="100%" cellpadding="0" cellspacing="0" style="background:{_CARD};border:1px solid {_BORDER};">
<tr><td style="padding:24px 32px;">
  <h2 style="margin:0 0 14px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:16px;font-weight:700;color:{_BODY_TEXT};text-transform:uppercase;letter-spacing:1px;">Executive Brief</h2>
  {paragraphs}
  {theme_badges}
</td></tr></table>'''

    # --- Editor's Pick ---
    pick_html = ""
    if pick_id:
        pick_item = None
        for item in all_items:
            if item["id"] == pick_id:
                pick_item = item
                break
        if pick_item:
            pick_summary = item_summaries.get(pick_id, "") if item_summaries else ""
            pick_html = f'''<table width="100%" cellpadding="0" cellspacing="0" style="background:{_PICK_BG};border-left:4px solid {_ACCENT};margin-top:2px;">
<tr><td style="padding:18px 28px;">
  <p style="margin:0 0 4px;font-family:-apple-system,sans-serif;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:{_ACCENT};">\u2b50 Editor's Pick</p>
  <a href="{escape(pick_item['url'])}" target="_blank" style="font-family:Georgia,'Times New Roman',serif;font-size:17px;font-weight:700;color:{_BODY_TEXT};text-decoration:none;">{escape(pick_item['title'])}</a>
  {f'<p style="margin:6px 0 0;font-family:-apple-system,sans-serif;font-size:13px;color:{_MUTED};font-style:italic;">{escape(pick_reason)}</p>' if pick_reason else ''}
  {f'<p style="margin:8px 0 0;font-family:Georgia,serif;font-size:14px;line-height:1.6;color:{_BODY_TEXT};">{escape(pick_summary)}</p>' if pick_summary else ''}
</td></tr></table>'''

    # --- Category Sections ---
    grouped = _group_by_category(all_items)
    categories_html = ""
    for cat_key, cat_label in CATEGORIES:
        cat_items = grouped.get(cat_key, [])
        if not cat_items:
            continue
        categories_html += _render_category_section(
            cat_key, cat_label, cat_items,
            tldr_map, item_summaries or {}, section_stats, pick_id
        )

    # --- Footer ---
    footer = f'''<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:2px;">
<tr><td style="padding:20px 32px;text-align:center;">
  <p style="margin:0;font-family:-apple-system,sans-serif;font-size:12px;color:{_MUTED};">
    The Anime AI Digest &middot; <a href="{REPO_URL}" target="_blank" style="color:{_ACCENT};text-decoration:none;">Source</a>
  </p>
  <p style="margin:4px 0 0;font-family:-apple-system,sans-serif;font-size:11px;color:{_MUTED};opacity:0.6;">
    Curated with AI, built for creators.
  </p>
</td></tr></table>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Anime AI Digest — {date_str}</title>
<style>
body{{margin:0;padding:0;background:{_BG};}}
a:hover{{opacity:0.8;}}
@media(max-width:680px){{
  .bulletin-wrap{{width:100%!important;}}
}}
</style>
</head>
<body style="margin:0;padding:0;background:{_BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;">
<center>
<table class="bulletin-wrap" width="640" cellpadding="0" cellspacing="0" style="margin:20px auto;background:{_BG};max-width:640px;">
<tr><td>
{masthead}
{brief_html}
{pick_html}
{categories_html}
{footer}
</td></tr>
</table>
</center>
</body>
</html>'''


# =============================================================================
# MAIN ENTRY
# =============================================================================

def run_renderer(run_id: str, summary_data: dict | None = None) -> dict:
    """Generate bulletin digest from scored items."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Get all scored items — need enough to ensure category diversity after cap
    scored_items = supabase_client.get_top_scored_items(run_id, limit=1000)
    scored_items = apply_source_cap(scored_items)
    logger.info(f"Rendering {len(scored_items)} items for {date_str} (after source cap)")

    # Load per-item summaries from DB
    item_summaries: dict[str, str] = {}
    try:
        item_summaries = supabase_client.get_summaries_by_run(run_id)
        if item_summaries:
            logger.info(f"Loaded {len(item_summaries)} per-item summaries")
    except Exception as e:
        logger.warning(f"Failed to load summaries: {e}")

    # Flatten items in score order
    all_items = [_get_item_data(score_row) for score_row in scored_items]

    # Render
    md_content = _render_markdown(date_str, all_items, summary_data, item_summaries)
    html_content = _render_bulletin_html(date_str, all_items, summary_data, item_summaries)

    # Write files
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = OUTPUT_DIR / f"{date_str}.md"
    html_path = OUTPUT_DIR / f"{date_str}.html"

    md_path.write_text(md_content, encoding="utf-8")
    html_path.write_text(html_content, encoding="utf-8")

    logger.info(f"Written: {md_path}, {html_path}")

    # Update run
    supabase_client.update_run(run_id, {
        "output_md": str(md_path),
        "output_html": str(html_path),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })

    result = {"md_path": str(md_path), "html_path": str(html_path)}
    logger.info(f"Renderer complete: {result}")
    return result


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not run_id:
        logger.error("Usage: python -m agents.renderer.main <run_id>")
        sys.exit(1)
    result = run_renderer(run_id)
    logger.info(f"Renderer complete: {result}")
