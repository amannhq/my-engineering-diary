"""Helpers to build payloads for the OpenAI Responses API."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


DAILY_ANALYSIS_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "001-you-are-expert"
    / "contracts"
    / "daily-analysis.schema.json"
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _baseline_step(summary: str) -> Dict[str, Any]:
    return {
        "index": 1,
        "title": "Pending Analysis",
        "summary": summary or "Awaiting LLM analysis",
        "timestamp": _utc_timestamp(),
    }


def _sanitize_artifact_path(path: str | None) -> str:
    return path or ""


def _aggregate_warnings(goal_ids: Iterable[str], sanitization_report: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    if sanitization_report.get("is_redacted") is not True:
        warnings.append("Sanitization did not confirm redaction")
    missing_goals = sanitization_report.get("missing_goals")
    if missing_goals:
        warnings.append(f"Missing goals: {', '.join(sorted(missing_goals))}")
    if not goal_ids:
        warnings.append("No goal references provided for log")
    return warnings


def build_payload(
    log_path: Path,
    sanitized_markdown: str,
    goal_ids: List[str],
    summary: str,
    analysis_config: Dict[str, Any],
    sanitization_report: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Return a payload compatible with `daily-analysis.schema.json`."""

    report = sanitization_report or {}

    payload: Dict[str, Any] = {
        "logRef": str(log_path),
        "analysisSteps": [_baseline_step(summary)],
        "status": "INFO",
        "tokenUsage": {"prompt": 0, "completion": 0, "total": 0},
        "requestId": analysis_config.get("run_id", "pending"),
        "artifactPath": _sanitize_artifact_path(analysis_config.get("artifact_path")),
        "warnings": _aggregate_warnings(goal_ids, report),
    }

    payload.setdefault("metadata", {})
    payload["metadata"].update(
        {
            "goalIds": goal_ids,
            "sanitizationReport": report,
            "sanitizedMarkdown": sanitized_markdown,
        }
    )

    return payload
