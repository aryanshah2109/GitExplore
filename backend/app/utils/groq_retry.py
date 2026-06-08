"""Shared retry wrapper for Groq API calls."""

from __future__ import annotations

import logging
import time


logger = logging.getLogger("gitexplore")


def groq_completion_with_retry(
    client,
    model,
    messages,
    temperature,
    max_tokens,
    max_retries: int = 3,
    retry_delay: float = 1.25,
):
    """Call Groq chat completions with simple retry handling."""
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            last_error = exc
            error_text = str(exc).lower()
            if "429" not in error_text and "rate limit" not in error_text:
                break
            if attempt < max_retries:
                sleep_for = retry_delay * attempt
                logger.warning(
                    "Groq rate limit hit on attempt %d/%d; retrying in %.1fs",
                    attempt,
                    max_retries,
                    sleep_for,
                )
                time.sleep(sleep_for)

    raise RuntimeError(f"Groq call failed after {max_retries} attempts: {last_error}")
