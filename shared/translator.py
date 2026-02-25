"""
Translation wrapper with Supabase caching.

Uses deep-translator (GoogleTranslator) for CJK → English translation.
Caches results in Supabase translations table to avoid redundant API calls.

Usage:
    from shared.translator import translate_text
    english = translate_text("AI動画生成モデル", source_lang="ja")

See docs/SOURCE_EXPLORATION.md → Translation Strategy for details.
"""
# TODO: Implement
# pip install deep-translator
