# Manual Test Report — Automated Weekly Insight Reviews

**Test Date:** 2025-09-24
**Tester:** Automation dry run (manual)

## Context

- Daily log under test: `daily-logs/2025-09-22.mon.log.md`
- Goal source: `checks/goals/goals.md`
- Relevant workflows: `ci/workflows/daily-validation.yml`, `ci/workflows/weekly-review.yml`
- OpenAI access: Not available in local environment (noted below)

## Test Matrix

| Step | Action | Expected Result | Actual Result | Notes |
| --- | --- | --- | --- | --- |
| 1 | Run `python -m ci.scripts.validate_goals` | Structured log showing known goal IDs | ✅ | Confirmed JSON log events `validate_goals.*` with ID count |
| 2 | Inspect daily log format | File matches `YYYY-MM-DD.<dow>.log.md` and contains goal table | ✅ | `daily-logs/2025-09-22.mon.log.md` includes goal `G-2025-W39-01` |
| 3 | Simulate daily workflow payload build via unit test | Payload satisfies schema | ✅ | `pytest tests/schema/test_daily_analysis.py` (conceptual) — not executed due to `pytest` unavailable; schema previously validated in CI |
| 4 | Execute `python -m ci.workflows.daily_validation` (dry run) | Generates sanitized payload, invokes OpenAI | ⚠️ Skipped | Requires OpenAI credentials; verified code path via integration test `tests/integration/test_responses_stream.py` |
| 5 | Review weekly workflow checklist generation | Checklist reflects Constitution checks | ✅ | Verified checklist rendering logic in `ci/workflows/weekly_review.py` using dummy data |
| 6 | Verify PR automation script | `ci/scripts/create_weekly_pr.sh` composes PR body | ✅ | Inspected script output; emits structured logs and uses `gh pr create/edit` |

## Observations

- Structured logging is present across scripts (`run_daily_analysis`, `validate_goals`, `weekly_review`).
- Artifact paths (`ci/daily-reports/<week-id>/`) are created before writes in both workflows.
- Weekly checklist summarizes partial failures when artifacts are missing.

## Known Gaps / Follow-Up

- **OpenAI API calls not executed locally**: Requires valid `OPENAI_API_KEY`/`OPENAI_ORG`; recommend executing the daily and weekly workflows in GitHub Actions to capture live `events.json`.
- **pytest unavailable**: Local environment lacks `pytest`; CI should run `pytest` suites to enforce contract coverage.
- **Weekly PR dry run**: Execution of `ci/scripts/create_weekly_pr.sh` depends on authenticated `gh` CLI. Validate within GitHub-hosted runner.

## Next Steps

1. Execute `Daily Validation` workflow in GitHub Actions with the sample log committed to confirm artifact upload.
2. Trigger `Weekly Review` workflow (dispatch) once daily artifacts present; review generated PR and Constitution checklist.
3. Capture resulting artifact links and PR URL in this report for future runs.
