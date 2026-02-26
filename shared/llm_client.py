"""
Azure OpenAI client with retry logic.

Simplified wrapper around the OpenAI SDK for Azure-hosted models.
"""
import json
import logging
import random
import time

from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError

from shared import config

logger = logging.getLogger(__name__)

_client = None

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_BASE_DELAY = 2.0
_MAX_DELAY = 60.0


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.AZURE_OPENAI_BASE_URL or not config.AZURE_OPENAI_API_KEY:
            raise RuntimeError("AZURE_OPENAI_BASE_URL and AZURE_OPENAI_API_KEY must be set")
        _client = OpenAI(
            base_url=config.AZURE_OPENAI_BASE_URL,
            api_key=config.AZURE_OPENAI_API_KEY,
            timeout=120.0,
        )
    return _client


def generate(
    messages: list[dict],
    max_tokens: int = 2048,
    temperature: float = 0.3,
    response_format: dict | None = None,
) -> str:
    """Call the LLM and return the content string. Retries on transient errors."""
    client = _get_client()
    kwargs = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format:
        kwargs["response_format"] = response_format

    for attempt in range(_MAX_RETRIES):
        try:
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except RateLimitError as e:
            delay = _backoff_delay(attempt, e)
            logger.warning(f"Rate limited (attempt {attempt + 1}/{_MAX_RETRIES}), retrying in {delay:.1f}s")
            time.sleep(delay)
        except (APITimeoutError, APIConnectionError) as e:
            delay = _backoff_delay(attempt)
            logger.warning(f"Transient error (attempt {attempt + 1}/{_MAX_RETRIES}): {e}, retrying in {delay:.1f}s")
            time.sleep(delay)
        except APIStatusError as e:
            if e.status_code in _RETRYABLE_STATUS_CODES:
                delay = _backoff_delay(attempt)
                logger.warning(f"Server error {e.status_code} (attempt {attempt + 1}/{_MAX_RETRIES}), retrying in {delay:.1f}s")
                time.sleep(delay)
            else:
                raise

    # Final attempt — let it raise
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


def _backoff_delay(attempt: int, error=None) -> float:
    """Exponential backoff with jitter. Respects Retry-After header if present."""
    if error and hasattr(error, "response") and error.response:
        retry_after = error.response.headers.get("Retry-After")
        if retry_after:
            try:
                return min(float(retry_after), _MAX_DELAY)
            except ValueError:
                pass
    delay = min(_BASE_DELAY * (2 ** attempt), _MAX_DELAY)
    jitter = delay * random.uniform(0.5, 1.5)
    return min(jitter, _MAX_DELAY)
