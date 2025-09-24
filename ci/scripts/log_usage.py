"""Append OpenAI token usage metrics for auditing."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

USAGE_CSV_PATH = Path("ci/daily-reports/usage.csv")


def _ensure_header(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["timestamp", "request_id", "prompt_tokens", "completion_tokens", "total_tokens"])


def append_usage(request_id: str, usage: Dict[str, int]) -> Path:
    """Append a row to the usage CSV and return the file path."""

    prompt = int(usage.get("prompt", usage.get("prompt_tokens", 0)) or 0)
    completion = int(usage.get("completion", usage.get("completion_tokens", 0)) or 0)
    total = int(usage.get("total", usage.get("total_tokens", prompt + completion)) or (prompt + completion))

    _ensure_header(USAGE_CSV_PATH)
    with USAGE_CSV_PATH.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                datetime.now(timezone.utc).isoformat(),
                request_id,
                prompt,
                completion,
                total,
            ]
        )

    return USAGE_CSV_PATH
