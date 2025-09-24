"""Utilities supporting the daily validation workflow."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from ci.sanitizers.redact_personal_info import EMAIL_PATTERN, NAME_PATTERN, sanitize_markdown
from ci.scripts.prepare_responses_payload import build_payload
from ci.scripts.run_responses_analysis import run_daily_analysis
from ci.scripts.log_usage import append_usage

try:  # pragma: no cover - placeholder until T017 implemented
    from ci.scripts.validate_goals import ensure_goal_ids_exist, GoalValidationError
except ImportError:  # pragma: no cover
    class GoalValidationError(RuntimeError):
        pass

    def ensure_goal_ids_exist(goal_ids: Iterable[str]) -> None:
        if not goal_ids:
            raise GoalValidationError("Goal validation not implemented")

GOAL_ID_PATTERN = re.compile(r"G-\d{4}-W\d{2}-\d{2}")


def _emit_log(event: str, **payload: Any) -> None:
    entry: Dict[str, Any] = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "event": event,
        **payload,
    }
    print(json.dumps(entry, default=str))


def extract_goal_ids(markdown: str) -> List[str]:
    return sorted(set(GOAL_ID_PATTERN.findall(markdown)))


def load_log(log_path: Path) -> str:
    return log_path.read_text(encoding="utf-8")


def sanitize_log(log_path: Path) -> Tuple[str, Dict[str, Any]]:
    raw = load_log(log_path)
    sanitized = sanitize_markdown(raw)

    removed_emails = list(sorted(set(EMAIL_PATTERN.findall(raw))))
    removed_names = []
    if "[REDACTED_NAME]" in sanitized:
        candidates = set(NAME_PATTERN.findall(raw))
        removed_names = sorted(candidates)

    report = {
        "is_redacted": sanitized != raw,
        "removed_emails": removed_emails,
        "removed_names": removed_names,
    }
    return sanitized, report


def build_daily_payload(
    log_path: Path,
    sanitized_markdown: str,
    goal_ids: List[str],
    summary: str,
    sanitization_report: Dict[str, Any],
) -> Dict[str, Any]:
    return build_payload(
        log_path=log_path,
        sanitized_markdown=sanitized_markdown,
        goal_ids=goal_ids,
        summary=summary,
        analysis_config={"run_id": f"daily-{log_path.stem}"},
        sanitization_report=sanitization_report,
    )


def process_log(
    log_path: Path,
    metadata: Dict[str, Any] | Iterable[str] | None = None,
) -> Dict[str, Any]:
    goal_ids_override: Iterable[str] | None = None
    if metadata is None:
        metadata_dict: Dict[str, Any] = {}
    elif isinstance(metadata, dict):
        metadata_dict = dict(metadata)
    else:
        goal_ids_override = list(metadata)
        metadata_dict = {}

    _emit_log(
        "process_log.start",
        log=str(log_path),
        metadata_keys=sorted(metadata_dict.keys()),
        goal_override=list(goal_ids_override or []),
    )
    raw = load_log(log_path)
    _emit_log("process_log.loaded", log=str(log_path), characters=len(raw))
    goal_ids = extract_goal_ids(raw)
    if goal_ids_override:
        goal_ids = sorted(set(goal_ids_override))
    ensure_goal_ids_exist(goal_ids)
    _emit_log("process_log.goal_ids_valid", log=str(log_path), goal_ids=goal_ids)

    sanitized_markdown, report = sanitize_log(log_path)
    _emit_log(
        "process_log.sanitized",
        log=str(log_path),
        is_redacted=report.get("is_redacted"),
        removed_emails=len(report.get("removed_emails", [])),
        removed_names=len(report.get("removed_names", [])),
    )

    payload = build_daily_payload(
        log_path=log_path,
        sanitized_markdown=sanitized_markdown,
        goal_ids=goal_ids,
        summary=metadata_dict.get("summary", ""),
        sanitization_report=report,
    )
    _emit_log(
        "process_log.payload_built",
        log=str(log_path),
        request_id=payload.get("requestId"),
        warnings=payload.get("warnings", []),
    )

    analysis_result = run_daily_analysis(
        log_path=log_path,
        sanitized_markdown=sanitized_markdown,
        goal_ids=goal_ids,
        metadata={
            **metadata_dict,
            "sanitization_report": report,
            "artifact_path": payload.get("artifactPath"),
        },
    )
    _emit_log(
        "process_log.analysis_completed",
        log=str(log_path),
        request_id=analysis_result.get("request_id"),
        events_path=str(analysis_result.get("events_path")),
        steps=len(analysis_result.get("steps", [])),
    )

    usage_path = append_usage(
        analysis_result.get("request_id", ""),
        analysis_result.get("usage", {}),
    )
    _emit_log(
        "process_log.usage_recorded",
        log=str(log_path),
        usage_path=str(usage_path),
    )

    return {
        "payload": payload,
        "result": analysis_result,
        "usage_path": usage_path,
    }


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run daily diary validation")
    parser.add_argument("--log-path", required=True, help="Path to daily log file")
    parser.add_argument("--summary", default="", help="Optional summary for baseline step")
    parser.add_argument("--artifact-dir", help="Directory to store analysis artifacts")
    parser.add_argument("--model", default="gpt-4.1", help="Responses API model name")
    parser.add_argument("--run-id", help="Override run identifier")
    args = parser.parse_args(argv)

    log_path = Path(args.log_path)
    metadata: Dict[str, Any] = {
        "summary": args.summary,
        "model": args.model,
    }
    if args.run_id:
        metadata["run_id"] = args.run_id
    else:
        metadata["run_id"] = f"daily-{log_path.stem}"
    if args.artifact_dir:
        metadata["artifact_dir"] = args.artifact_dir
        metadata["artifact_path"] = args.artifact_dir

    result = process_log(log_path, metadata)

    output = {
        "log_path": str(log_path),
        "request_id": result["result"].get("request_id"),
        "steps": result["result"].get("steps", []),
        "events_path": str(result["result"].get("events_path")),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
