from pathlib import Path


def test_process_log_sanitizes_before_analysis(monkeypatch):
    from ci.workflows import daily_validation

    calls = []

    def fake_sanitize(log_path: Path):
        calls.append("sanitize")
        return "sanitized", {"is_redacted": True}

    def fake_payload(*args, **kwargs):
        calls.append("payload")
        return {"logRef": str(args[0])}

    def fake_run(*args, **kwargs):
        calls.append("run")

    monkeypatch.setattr(daily_validation, "sanitize_log", fake_sanitize)
    monkeypatch.setattr(daily_validation, "build_daily_payload", fake_payload)
    monkeypatch.setattr(daily_validation, "run_daily_analysis", fake_run)

    daily_validation.process_log(Path("daily-logs/2025-09-22.mon.log.md"), ["G-2025-W39-01"])

    assert calls == ["sanitize", "payload", "run"]
