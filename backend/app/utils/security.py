"""
Security utilities — input sanitization and rate limiting.
"""

import re

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

settings = get_settings()

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent injection attacks.

    - Strips leading/trailing whitespace
    - Removes HTML tags
    - Removes control characters
    - Limits length
    """
    # Strip whitespace
    text = text.strip()

    # Remove HTML/XML tags
    text = re.sub(r"<[^>]*>", "", text)

    # Remove control characters (keep newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Remove potential script injection patterns
    text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"on\w+\s*=", "", text, flags=re.IGNORECASE)

    return text


def validate_topic(topic: str) -> str:
    """Validate and sanitize a research topic."""
    topic = sanitize_input(topic)

    if len(topic) < 3:
        raise ValueError("Research topic must be at least 3 characters.")
    if len(topic) > 500:
        raise ValueError("Research topic must be at most 500 characters.")

    return topic
