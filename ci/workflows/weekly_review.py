"""Utilities for generating weekly insight reports from daily automation artifacts."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from weekly_review.aggregator import render_weekly_report

from ci.workflows.daily_validation import extract_goal_ids, process_log
from ci.scripts.log_usage import append_usage
from ci.scripts.run_responses_analysis import get_openai_client
from ci.scripts.validate_goals import GoalValidationError, ensure_goal_ids_exist

DAILY_REPORTS_DIR = Path("ci/daily-reports")
USAGE_CSV_PATH = DAILY_REPORTS_DIR / "usage.csv"
WEEKLY_PROMPT_PATH = Path("ci/prompts/weekly-synthesis.md")
WEEKLY_REVIEW_DIR = Path("weekly-review")
DAILY_LOGS_DIR = Path("daily-logs")

LOG_FILENAME_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.[a-z]{3}\.log\.md$")


def _emit_log(event: str, **payload: Any) -> None:
    entry: Dict[str, Any] = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "event": event,
        **payload,
    }
    print(json.dumps(entry, default=str))


def _week_id_from_date(date: dt.date) -> str:
    iso = date.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _default_week_id(today: dt.date | None = None) -> str:
    today = today or dt.date.today()
    # When running on Sunday, report on the completed week (Monday-Saturday)
    if today.weekday() == 6:  # Sunday
        target = today - dt.timedelta(days=1)
    else:
        target = today
    return _week_id_from_date(target)


def _parse_log_date(log_path: Path) -> dt.date | None:
    match = LOG_FILENAME_PATTERN.match(log_path.name)
    if not match:
        return None
    year, month, day = map(int, match.groups())
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def _load_usage_map(path: Path = USAGE_CSV_PATH) -> Dict[str, Dict[str, int]]:
    if not path.exists():
        return {}

    usage: Dict[str, Dict[str, int]] = {}
    with path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            request_id = row.get("request_id") or ""
            if not request_id:
                continue
            usage[request_id] = {
                "prompt": int(row.get("prompt_tokens", "0") or 0),
                "completion": int(row.get("completion_tokens", "0") or 0),
                "total": int(row.get("total_tokens", "0") or 0),
            }
    return usage


def _parse_summary(summary_path: Path) -> Dict[str, Any]:
    content = summary_path.read_text(encoding="utf-8")
    log_ref = ""
    request_id = ""
    steps: List[str] = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith("- Log:"):
            log_ref = line.split(":", 1)[1].strip()
        elif line.startswith("- Request ID:"):
            request_id = line.split(":", 1)[1].strip()
        elif line.startswith("- Steps:"):
            steps_str = line.split(":", 1)[1].strip()
            if steps_str:
                steps = [segment.strip() for segment in steps_str.split(",") if segment.strip()]

    return {
        "log_ref": log_ref,
        "request_id": request_id,
        "steps": steps,
    }


def _collect_daily_artifacts(week_id: str, reports_dir: Path = DAILY_REPORTS_DIR) -> List[Dict[str, Any]]:
    prefix = f"{week_id}-"
    usage_map = _load_usage_map()

    artifacts: List[Dict[str, Any]] = []
    if not reports_dir.exists():
        return artifacts

    for day_dir in sorted(p for p in reports_dir.iterdir() if p.is_dir() and p.name.startswith(prefix)):
        summary_path = day_dir / "summary.md"
        events_path = day_dir / "events.json"
        if not summary_path.exists():
            continue

        details = _parse_summary(summary_path)
        request_id = details.get("request_id", "")
        token_usage = usage_map.get(request_id, {"prompt": 0, "completion": 0, "total": 0})

        artifacts.append(
            {
                "log_ref": details.get("log_ref"),
                "summary_path": summary_path,
                "events_path": events_path if events_path.exists() else None,
                "steps": details.get("steps", []),
                "token_usage": token_usage,
                "request_id": request_id,
            }
        )

    return artifacts


def _identify_partial_failures(artifacts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []
    for artifact in artifacts:
        issues: List[str] = []
        log_ref = str(artifact.get("log_ref", "unknown"))
        request_id = artifact.get("request_id")
        steps = artifact.get("steps") or []
        events_path = artifact.get("events_path")

        if not request_id:
            issues.append("missing Responses request ID")
        if not steps:
            issues.append("no streamed steps captured")
        if not events_path or not Path(events_path).exists():
            issues.append("events.json artifact missing")

        if issues:
            failures.append({
                "log_ref": log_ref,
                "issues": issues,
                "events_path": str(events_path) if events_path else "",
            })
    return failures


def _week_slug(week_id: str) -> str:
    parts = week_id.split("-")
    if len(parts) >= 2 and parts[1].lower().startswith("w"):
        week_num = parts[1][1:]
    else:
        week_num = week_id
    return f"week-{week_num.lower()}"


def _checklist_path(week_id: str, weekly_dir: Path) -> Path:
    return weekly_dir / f"{_week_slug(week_id)}-checklist.md"


def _render_checklist(
    week_id: str,
    goal_progress: Sequence[Dict[str, Any]],
    partial_failures: Sequence[Dict[str, Any]],
) -> str:
    constitution_items: List[Tuple[str, str]] = [
        ("P1 Daily Log Fidelity", "Daily logs validated and referenced goals confirmed."),
        ("P2 Goal-Aligned Reflection", "Weekly synthesis references goal progress."),
        ("P3 Automated Insight Pipeline", "Daily and weekly automations executed."),
        ("P4 Transparent LLM Execution", "Artifacts and streaming events captured."),
        ("P5 Markdown as Source of Truth", "Outputs stored in repository Markdown files."),
    ]

    all_clear = not partial_failures
    lines: List[str] = [
        f"# Weekly Review Checklist — {week_id}",
        "",
        "## Constitution Principles",
    ]
    for title, desc in constitution_items:
        mark = "x" if all_clear else " "
        lines.append(f"- [{mark}] {title} — {desc}")

    lines.extend([
        "",
        "## Goal Progress",
    ])
    if goal_progress:
        for entry in goal_progress:
            gid = entry.get("goal_id", "UNKNOWN")
            status = entry.get("status", "Unknown")
            lines.append(f"- {gid}: {status}")
    else:
        lines.append("- No goal updates detected.")

    lines.extend(["", "## Partial Failures"])
    if partial_failures:
        for failure in partial_failures:
            issues = "; ".join(failure.get("issues", []))
            lines.append(f"- {failure.get('log_ref', 'unknown')}: {issues}")
    else:
        lines.append("- None detected.")

    lines.extend([
        "",
        "## Action Items",
        "- Verify checklist items above and resolve any partial failures before merging.",
        "- Ensure weekly PR references this checklist file.",
    ])

    return "\n".join(lines) + "\n"


def _write_checklist(
    week_id: str,
    weekly_dir: Path,
    goal_progress: Sequence[Dict[str, Any]],
    partial_failures: Sequence[Dict[str, Any]],
) -> Path:
    path = _checklist_path(week_id, weekly_dir)
    content = _render_checklist(week_id, goal_progress, partial_failures)
    path.write_text(content, encoding="utf-8")
    _emit_log("weekly.checklist_written", week_id=week_id, checklist=str(path))
    return path


def _artifact_dir_for_log(log_path: Path, week_id: str) -> Path:
    log_date = _parse_log_date(log_path)
    if not log_date:
        raise ValueError(f"Unable to derive date from log filename: {log_path}")
    iso_week = log_date.isocalendar()
    tag = f"{iso_week.year}-W{iso_week.week:02d}-{log_date.day:02d}"
    return DAILY_REPORTS_DIR / tag


def _find_week_logs(week_id: str, logs_dir: Path = DAILY_LOGS_DIR) -> List[Path]:
    if not logs_dir.exists():
        return []

    target_year, target_week = week_id.split("-W")
    target_year_int = int(target_year)
    target_week_int = int(target_week)

    matches: List[Path] = []
    for path in sorted(logs_dir.glob("*.log.md")):
        log_date = _parse_log_date(path)
        if not log_date:
            continue
        iso = log_date.isocalendar()
        if iso.year == target_year_int and iso.week == target_week_int:
            matches.append(path)
    return matches


def _ensure_daily_artifacts(week_id: str, logs: Sequence[Path]) -> List[Dict[str, Any]]:
    artifacts: List[Dict[str, Any]] = []

    for log_path in logs:
        artifact_dir = _artifact_dir_for_log(log_path, week_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Skip regeneration if summary already exists
        summary_path = artifact_dir / "summary.md"
        events_path = artifact_dir / "events.json"
        if not summary_path.exists() or not events_path.exists():
            result = process_log(
                log_path=log_path,
                metadata={
                    "summary": f"Automated weekly aggregation for {log_path.name}",
                    "artifact_dir": str(artifact_dir),
                    "run_id": f"weekly-{log_path.stem}",
                },
            )

            summary_path.write_text(
                "\n".join(
                    [
                        "# Daily Analysis",
                        "",
                        f"- Log: {log_path}",
                        f"- Request ID: {result['result'].get('request_id')}",
                        "- Steps: "
                        + ", ".join(result["result"].get("steps", [])),
                    ]
                ),
                encoding="utf-8",
            )

        details = _parse_summary(summary_path)
        request_id = details.get("request_id", "")
        token_usage = _load_usage_map().get(request_id, {"prompt": 0, "completion": 0, "total": 0})

        artifacts.append(
            {
                "log_ref": details.get("log_ref"),
                "summary_path": summary_path,
                "events_path": events_path if events_path.exists() else None,
                "steps": details.get("steps", []),
                "token_usage": token_usage,
                "request_id": request_id,
            }
        )

    return artifacts


def _build_goal_progress(artifacts: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
    goal_ids: set[str] = set()

    for artifact in artifacts:
        log_ref = artifact.get("log_ref")
        if not log_ref:
            continue
        log_path = Path(log_ref)
        if not log_path.exists():
            continue
        try:
            content = log_path.read_text(encoding="utf-8")
        except OSError:
            continue
        goal_ids.update(extract_goal_ids(content))

    if not goal_ids:
        return []

    ensure_goal_ids_exist(goal_ids)

    return [
        {"goal_id": goal_id, "status": "Pending review"}
        for goal_id in sorted(goal_ids)
    ]


def _collect_content_deltas(events: Iterable[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for event in events:
        if event.get("type") == "response.output_text.delta":
            delta = event.get("delta")
            if delta:
                parts.append(delta)
    return "".join(parts)


def _extract_request_id(events: Iterable[Dict[str, Any]]) -> str:
    for event in events:
        if event.get("type") == "response.completed":
            response = event.get("response") or {}
            request_id = response.get("id")
            if request_id:
                return request_id
    return ""


def _extract_usage(events: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    for event in events:
        if event.get("type") == "response.completed":
            response = event.get("response") or {}
            usage = response.get("usage") or {}
            return {
                "prompt": int(usage.get("prompt_tokens", 0) or 0),
                "completion": int(usage.get("completion_tokens", 0) or 0),
                "total": int(usage.get("total_tokens", 0) or 0),
            }
    return {"prompt": 0, "completion": 0, "total": 0}


def _create_weekly_summary(
    week_id: str,
    artifacts: Sequence[Dict[str, Any]],
    model: str = "gpt-4.1",
    prompt_path: Path = WEEKLY_PROMPT_PATH,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if not artifacts:
        return {
            "summary": "No daily artifacts were available for the requested week.",
            "usage": {"prompt": 0, "completion": 0, "total": 0},
            "request_id": "",
            "events": [],
        }

    metadata = metadata or {}
    client = get_openai_client()

    try:
        system_prompt = prompt_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"Unable to read weekly prompt from {prompt_path}: {exc}")

    lines: List[str] = [f"Week ID: {week_id}", "Daily Artifacts:"]
    for artifact in artifacts:
        log_ref = artifact.get("log_ref", "unknown")
        steps = artifact.get("steps") or []
        token_usage = artifact.get("token_usage") or {}
        lines.append(f"- Log: {log_ref}")
        if steps:
            lines.append(f"  Steps: {' | '.join(steps)}")
        else:
            lines.append("  Steps: Not recorded")
        lines.append(
            "  Token Usage: prompt={prompt} completion={completion} total={total}".format(
                prompt=token_usage.get("prompt", 0),
                completion=token_usage.get("completion", 0),
                total=token_usage.get("total", 0),
            )
        )
    context = "\n".join(lines)

    events = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ],
        metadata={"weekId": week_id, **metadata},
    )

    events_list = list(events)
    summary_text = _collect_content_deltas(events_list)
    request_id = _extract_request_id(events_list)
    usage = _extract_usage(events_list)

    return {
        "summary": summary_text.strip() or "Weekly synthesis did not return any content.",
        "usage": usage,
        "request_id": request_id,
        "events": events_list,
    }


def process_week(
    week_id: str,
    reports_dir: Path = DAILY_REPORTS_DIR,
    weekly_dir: Path = WEEKLY_REVIEW_DIR,
    model: str = "gpt-4.1",
    prompt_path: Path = WEEKLY_PROMPT_PATH,
) -> Dict[str, Any]:
    _emit_log("weekly.process.start", week_id=week_id, reports_dir=str(reports_dir), weekly_dir=str(weekly_dir))
    week_logs = _find_week_logs(week_id)
    _emit_log("weekly.logs.discovered", week_id=week_id, log_count=len(week_logs))
    regenerated_artifacts = _ensure_daily_artifacts(week_id, week_logs)
    artifacts = regenerated_artifacts or _collect_daily_artifacts(week_id, reports_dir=reports_dir)
    _emit_log("weekly.artifacts.ready", week_id=week_id, artifact_count=len(artifacts))
    goal_progress: List[Dict[str, str]] = []
    try:
        goal_progress = _build_goal_progress(artifacts)
    except GoalValidationError as exc:
        goal_progress = [{"goal_id": "N/A", "status": f"Validation error: {exc}"}]

    partial_failures = _identify_partial_failures(artifacts)
    _emit_log("weekly.partial_failures", week_id=week_id, partial_count=len(partial_failures))

    synthesis = _create_weekly_summary(
        week_id=week_id,
        artifacts=artifacts,
        model=model,
        prompt_path=prompt_path,
    )

    if synthesis.get("request_id"):
        append_usage(synthesis["request_id"], synthesis.get("usage", {}))

    weekly_artifact_dir = reports_dir / week_id
    weekly_artifact_dir.mkdir(parents=True, exist_ok=True)

    events_path = weekly_artifact_dir / "weekly-events.json"
    events_path.write_text(json.dumps(synthesis.get("events", []), indent=2), encoding="utf-8")

    summary_path = weekly_artifact_dir / "summary.md"
    summary_path.write_text(synthesis.get("summary", ""), encoding="utf-8")

    report_path = render_weekly_report(
        week_id=week_id,
        daily_artifacts=artifacts,
        goals_progress=goal_progress,
        output_dir=weekly_dir,
        llm_summary=synthesis.get("summary"),
    )

    checklist_path = _write_checklist(
        week_id=week_id,
        weekly_dir=weekly_dir,
        goal_progress=goal_progress,
        partial_failures=partial_failures,
    )

    _emit_log(
        "weekly.process.completed",
        week_id=week_id,
        report=str(report_path),
        checklist=str(checklist_path),
        partial_failures=len(partial_failures),
    )

    return {
        "report_path": report_path,
        "artifact_count": len(artifacts),
        "goal_progress": goal_progress,
        "events_path": events_path,
        "summary_path": summary_path,
        "request_id": synthesis.get("request_id", ""),
        "partial_failures": partial_failures,
        "checklist_path": checklist_path,
        "week_slug": _week_slug(week_id),
        "usage": synthesis.get("usage", {}),
    }


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate weekly insight report from daily artifacts")
    parser.add_argument("--week-id", help="Target ISO week identifier (e.g., 2025-W39)")
    parser.add_argument("--reports-dir", default=str(DAILY_REPORTS_DIR), help="Directory containing daily report artifacts")
    parser.add_argument("--weekly-dir", default=str(WEEKLY_REVIEW_DIR), help="Directory to write weekly review Markdown")
    parser.add_argument("--model", default="gpt-4.1", help="OpenAI Responses API model name")
    parser.add_argument("--prompt-path", default=str(WEEKLY_PROMPT_PATH), help="Path to weekly synthesis prompt template")
    args = parser.parse_args(argv)

    week_id = args.week_id or _default_week_id()

    result = process_week(
        week_id=week_id,
        reports_dir=Path(args.reports_dir),
        weekly_dir=Path(args.weekly_dir),
        model=args.model,
        prompt_path=Path(args.prompt_path),
    )

    output = {
        "week_id": week_id,
        "report_path": str(result["report_path"]),
        "checklist_path": str(result["checklist_path"]),
        "artifact_count": result["artifact_count"],
        "goal_progress_entries": len(result["goal_progress"]),
        "partial_failures": len(result["partial_failures"]),
        "request_id": result.get("request_id"),
        "partial_failures_detail": result.get("partial_failures", []),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
