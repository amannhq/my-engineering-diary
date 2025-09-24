from weekly_review import aggregator


def test_weekly_report_links_daily_artifacts(tmp_path):
    reports_dir = tmp_path / "weekly-review"
    reports_dir.mkdir()

    daily_artifacts = [
        {
            "log_ref": "daily-logs/2025-09-22.mon.log.md",
            "summary_path": tmp_path / "ci" / "daily-reports" / "2025-W39-22" / "summary.md",
            "token_usage": {"prompt": 100, "completion": 50, "total": 150},
        },
        {
            "log_ref": "daily-logs/2025-09-23.tue.log.md",
            "summary_path": tmp_path / "ci" / "daily-reports" / "2025-W39-23" / "summary.md",
            "token_usage": {"prompt": 90, "completion": 40, "total": 130},
        },
    ]

    week_id = "2025-W39"

    resulting_path = aggregator.render_weekly_report(
        week_id=week_id,
        daily_artifacts=daily_artifacts,
        goals_progress=[{"goal_id": "G-2025-W39-01", "status": "On Track"}],
        output_dir=reports_dir,
    )

    expected_path = reports_dir / "week-39.md"
    assert resulting_path == expected_path

    content = expected_path.read_text()
    assert "G-2025-W39-01" in content
    for artifact in daily_artifacts:
        assert artifact["log_ref"] in content
        assert str(artifact["summary_path"]) in content

    assert "Total Tokens: 280" in content
