import json
from pathlib import Path
from unittest import mock


def _fake_events():
    return [
        {"type": "response.input_text.delta", "delta": "Analyzing"},
        {
            "type": "response.output_text.delta",
            "delta": "Step 1: Summarize goals",
        },
        {
            "type": "response.completed",
            "response": {
                "id": "resp_123",
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Daily summary",
                            }
                        ]
                    }
                ],
            },
        },
    ]


def test_run_daily_analysis_streams_and_saves_events(tmp_path, monkeypatch):
    from ci.scripts import run_responses_analysis

    out_dir = tmp_path / "ci" / "daily-reports" / "2025-W39-22"
    out_dir.mkdir(parents=True, exist_ok=True)

    fake_client = mock.Mock()
    events = _fake_events()
    fake_client.responses.create.return_value = events

    monkeypatch.setattr(run_responses_analysis, "get_openai_client", lambda: fake_client)

    result = run_responses_analysis.run_daily_analysis(
        log_path=Path("daily-logs/2025-09-22.mon.log.md"),
        sanitized_markdown="# Log\n",
        goal_ids=["G-2025-W39-01"],
        metadata={"week_id": "2025-W39", "artifact_dir": out_dir},
    )

    events_file = out_dir / "events.json"
    assert events_file.exists()
    assert json.loads(events_file.read_text()) == events

    assert result["request_id"] == "resp_123"
    assert result["steps"] == ["Step 1: Summarize goals"]
    fake_client.responses.create.assert_called_once()
