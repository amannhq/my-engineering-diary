"""Goal file validation utilities."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Set

GOAL_FILE = Path(os.getenv("DIARY_GOALS_FILE", "checks/goals/goals.md"))
GOAL_ID_PATTERN = re.compile(r"^G-\d{4}-W\d{2}-\d{2}$")


class GoalValidationError(RuntimeError):
    """Raised when goal references are missing or malformed."""


def _emit_log(event: str, **payload: object) -> None:
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "event": event,
        **payload,
    }
    print(json.dumps(entry, default=str))


def _load_goal_ids(goal_file: Path = GOAL_FILE) -> Set[str]:
    _emit_log("validate_goals.load_start", goal_file=str(goal_file))
    if not goal_file.exists():
        raise GoalValidationError(f"Goal file missing at {goal_file}")

    goal_ids: Set[str] = set()
    for line in goal_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells and GOAL_ID_PATTERN.match(cells[0]):
                goal_ids.add(cells[0])
    if not goal_ids:
        raise GoalValidationError(f"No goal IDs found in {goal_file}")
    _emit_log("validate_goals.load_complete", goal_file=str(goal_file), count=len(goal_ids))
    return goal_ids


def ensure_goal_ids_exist(goal_ids: Iterable[str]) -> None:
    goal_ids = list(goal_ids)
    _emit_log("validate_goals.ensure_start", goal_ids=goal_ids)
    if not goal_ids:
        raise GoalValidationError("Daily log contains no goal references")

    known_ids = _load_goal_ids()
    unknown = [gid for gid in goal_ids if gid not in known_ids]
    if unknown:
        raise GoalValidationError(f"Unknown goal IDs referenced: {', '.join(sorted(unknown))}")
    _emit_log("validate_goals.ensure_success", goal_ids=goal_ids)


def _cli_validate(goal_ids: List[str] | None) -> None:
    _emit_log("validate_goals.cli_start", provided=goal_ids or [])
    known_ids = _load_goal_ids()
    if goal_ids:
        ensure_goal_ids_exist(goal_ids)
    _emit_log("validate_goals.cli_success", total=len(known_ids))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate goal definitions and optional references")
    parser.add_argument(
        "--goal-id",
        action="append",
        dest="goal_ids",
        help="Goal ID that must exist in the goals file (can be repeated)",
    )
    args = parser.parse_args(argv)

    try:
        _cli_validate(args.goal_ids)
    except GoalValidationError as exc:
        _emit_log("validate_goals.cli_failure", error=str(exc))
        print(f"::error ::{exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        _emit_log("validate_goals.cli_error", error=str(exc))
        print(f"::error ::Unexpected goal validation failure: {exc}")
        return 1

    _emit_log("validate_goals.cli_complete")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["ensure_goal_ids_exist", "GoalValidationError", "GOAL_FILE", "main"]
