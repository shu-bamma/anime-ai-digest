"""
Utility functions: hashing, date parsing, text cleaning.
"""
import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

from dateutil import parser as dateutil_parser
from bs4 import BeautifulSoup


def content_hash(source_id: str, url: str, title: str) -> str:
    """Generate SHA-256 hash for deduplication."""
    raw = f"{source_id}|{url}|{title}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_date(date_string: Optional[str]) -> Optional[datetime]:
    """Parse a date string into a UTC datetime. Returns None on failure."""
    if not date_string:
        return None
    try:
        dt = dateutil_parser.parse(date_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def now_utc_iso() -> str:
    """Current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def clean_html(html_string: str) -> str:
    """Strip HTML tags, return plain text."""
    if not html_string:
        return ""
    soup = BeautifulSoup(html_string, "lxml")
    return soup.get_text(separator=" ", strip=True)


def truncate(text: str, max_len: int = 500) -> str:
    """Truncate text to max_len characters."""
    if not text or len(text) <= max_len:
        return text or ""
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def is_cjk(text: str) -> bool:
    """Check if text contains CJK characters (Chinese/Japanese/Korean)."""
    for char in text:
        cp = ord(char)
        if (0x4E00 <= cp <= 0x9FFF or    # CJK Unified Ideographs
            0x3040 <= cp <= 0x309F or     # Hiragana
            0x30A0 <= cp <= 0x30FF or     # Katakana
            0xAC00 <= cp <= 0xD7AF):      # Hangul Syllables
            return True
    return False


def detect_language(text: str) -> str:
    """Simple language detection based on character ranges."""
    if not text:
        return "en"
    cjk_count = 0
    ja_count = 0
    ko_count = 0
    total = 0
    for char in text:
        cp = ord(char)
        if char.isalpha():
            total += 1
            if 0x4E00 <= cp <= 0x9FFF:
                cjk_count += 1
            elif 0x3040 <= cp <= 0x309F or 0x30A0 <= cp <= 0x30FF:
                ja_count += 1
            elif 0xAC00 <= cp <= 0xD7AF:
                ko_count += 1
    if total == 0:
        return "en"
    if ja_count > 0:
        return "ja"
    if ko_count > total * 0.3:
        return "ko"
    if cjk_count > total * 0.3:
        return "zh"
    return "en"
