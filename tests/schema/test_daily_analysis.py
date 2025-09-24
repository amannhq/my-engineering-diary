from pathlib import Path

import pytest
import json
import jsonschema

from ci.scripts.prepare_responses_payload import build_payload


@pytest.fixture
def daily_schema() -> dict:
    schema_path = Path(__file__).resolve().parents[2] / "specs" / "001-you-are-expert" / "contracts" / "daily-analysis.schema.json"
    if not schema_path.exists():  # pragma: no cover - defensive guard
        pytest.fail(f"Daily analysis schema missing at {schema_path}")
    return json.loads(schema_path.read_text())


def test_build_payload_matches_schema(daily_schema: dict) -> None:
    payload = build_payload(
        log_path=Path("daily-logs/2025-09-22.mon.log.md"),
        sanitized_markdown="# Log\n- accomplished: prototype\n",
        goal_ids=["G-2025-W39-01"],
        summary="Prototype progress",
        analysis_config={"run_id": "test-run"},
        sanitization_report={
            "is_redacted": True,
            "removed_names": ["Alice"],
            "removed_emails": ["alice@example.com"],
            "rules_version": "v1",
        },
    )

    jsonschema.validate(instance=payload, schema=daily_schema)

    assert payload["logRef"].endswith(".log.md")
    assert payload["tokenUsage"] == {"prompt": 0, "completion": 0, "total": 0}
