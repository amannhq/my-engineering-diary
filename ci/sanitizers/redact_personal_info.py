"""Sanitize diary markdown prior to sending to external APIs."""

from __future__ import annotations

import re
from typing import Iterable


EMAIL_PATTERN = re.compile(r"(?P<email>[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})")
NAME_PATTERN = re.compile(r"\b([A-Z][a-z]+)\b")
NAME_WHITELIST: set[str] = {
    "I",
    "Today",
    "Call",
    "Daily",
    "Weekly",
    "CI",
    "PR",
}


def _redact_emails(text: str) -> str:
    return EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)


def _candidate_names(tokens: Iterable[str]) -> set[str]:
    return {token for token in tokens if token and token[0].isupper() and token not in NAME_WHITELIST}


def _redact_names(text: str) -> str:
    candidates = _candidate_names(NAME_PATTERN.findall(text))
    if not candidates:
        return text

    def replace(match: re.Match[str]) -> str:
        word = match.group(0)
        if word in candidates:
            return "[REDACTED_NAME]"
        return word

    return NAME_PATTERN.sub(replace, text)


def sanitize_markdown(text: str) -> str:
    """Redact personal information to satisfy privacy guarantees."""

    sanitized = _redact_emails(text)
    sanitized = _redact_names(sanitized)
    return sanitized
