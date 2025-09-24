"""Render weekly review reports from daily automation artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List


def _week_filename(week_id: str) -> str:
    parts = week_id.split("-")
    if len(parts) >= 2 and parts[1].startswith("W"):
        week_num = parts[1][1:]
    else:
        week_num = week_id
    return f"week-{week_num.lower()}.md"


def _format_daily_section(artifact: Dict[str, object]) -> str:
    summary_path = artifact.get("summary_path")
    summary_link = f"{summary_path}" if summary_path else "(summary missing)"
    steps = artifact.get("steps", [])
    steps_text = " | ".join(steps) if steps else "No streamed steps recorded"
    return (
        f"### {artifact.get('log_ref', 'Unknown Log')}\n"
        f"- Summary file: {summary_link}\n"
        f"- Token usage: {artifact.get('token_usage')}\n"
        f"- Steps: {steps_text}\n"
    )


def _total_tokens(artifacts: Iterable[Dict[str, object]]) -> int:
    total = 0
    for artifact in artifacts:
        usage = artifact.get("token_usage") or {}
        total += int(usage.get("total", 0) or 0)
    return total


def render_weekly_report(
    week_id: str,
    daily_artifacts: List[Dict[str, object]],
    goals_progress: List[Dict[str, object]],
    output_dir: Path,
    llm_summary: str | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / _week_filename(week_id)

    total_tokens = _total_tokens(daily_artifacts)

    lines = [
        f"# Weekly Review — {week_id}",
        "",
    ]

    if llm_summary:
        lines.extend(["## Weekly Summary", llm_summary.strip(), ""])

    lines.append("## Goal Progress")
    if goals_progress:
        for entry in goals_progress:
            lines.append(
                f"- {entry.get('goal_id', 'UNKNOWN')}: {entry.get('status', 'Unknown status')}"
            )
    else:
        lines.append("- No goal updates provided.")
    lines.append("")

    lines.append("## Daily Highlights")
    if daily_artifacts:
        for artifact in daily_artifacts:
            lines.append(_format_daily_section(artifact))
    else:
        lines.append("No daily artifacts available for this week.")
    lines.append("")

    lines.append(f"## Metrics\n- Total Tokens: {total_tokens}")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


__all__ = ["render_weekly_report"]
