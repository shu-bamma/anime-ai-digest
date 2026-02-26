"""
Translation wrapper with Supabase caching.

Uses deep-translator (GoogleTranslator) for CJK -> English translation.
Caches results in Supabase translations table to avoid redundant API calls.
"""
import hashlib
import logging
import time
from typing import Optional

from deep_translator import GoogleTranslator

from shared import supabase_client
from shared.utils import is_cjk, detect_language

logger = logging.getLogger(__name__)

_translator = GoogleTranslator(source="auto", target="en")


def _text_hash(text: str, source_lang: str, target_lang: str = "en") -> str:
    raw = f"{text}|{source_lang}|{target_lang}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def translate_text(text: str, source_lang: Optional[str] = None, target_lang: str = "en") -> str:
    """
    Translate text to target language. Returns original if already in target or on failure.

    Checks Supabase cache first, then calls Google Translate, then caches result.
    """
    if not text or not text.strip():
        return text or ""

    if source_lang is None:
        source_lang = detect_language(text)

    if source_lang == target_lang:
        return text

    # Check cache
    th = _text_hash(text, source_lang, target_lang)
    try:
        cached = supabase_client.get_cached_translation(th, source_lang, target_lang)
        if cached:
            return cached
    except Exception as e:
        logger.debug(f"Cache lookup failed (ok, will translate): {e}")

    # Translate
    try:
        translated = _translator.translate(text)
        if not translated:
            return text
    except Exception as e:
        logger.warning(f"Translation failed for [{source_lang}] text: {e}")
        return text

    # Cache result
    try:
        supabase_client.cache_translation(th, text, source_lang, translated, target_lang)
    except Exception as e:
        logger.debug(f"Failed to cache translation: {e}")

    return translated


def translate_item(item: dict) -> dict:
    """
    Translate title and body of a FetchItem if non-English.
    Modifies item in-place and returns it.
    """
    lang = item.get("original_language", "en")
    if lang == "en":
        return item

    title = item.get("title", "")
    if title and is_cjk(title):
        item["title_translated"] = translate_text(title, source_lang=lang)
        # Small delay to respect rate limits
        time.sleep(0.2)

    body = item.get("raw_body", "")
    if body and is_cjk(body):
        # Only translate first 500 chars of body
        snippet = body[:500]
        item["body_translated"] = translate_text(snippet, source_lang=lang)
        time.sleep(0.2)

    return item
