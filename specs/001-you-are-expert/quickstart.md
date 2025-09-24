# Quickstart: Automated Weekly Insight Reviews

## Prerequisites
- GitHub repository with `daily-logs/` and `weekly-review/` directories.
- Secrets `OPENAI_API_KEY` and `OPENAI_ORG` configured in repository settings.
- Goal definitions in `checks/goals/goals.md` using `G-YYYY-W##-NN` identifiers.

## Daily Validation Workflow (Manual Trigger)
1. Create sample log `daily-logs/2025-09-22.mon.log.md` with goal references and sections (goals, steps, blockers, outcomes).
2. Push commit to branch and observe GitHub Action `ci/daily-validation.yml` run.
3. Confirm job outputs:
   - Streamed steps in action logs.
   - Sanitization script log showing redacted content.
   - Markdown artifact at `ci/daily-reports/2025-W39-22/summary.md`.
   - JSON event log at `ci/daily-reports/2025-W39-22/events.json`.

## Weekly Review Workflow (Manual Run)
1. Queue workflow dispatch for `ci/weekly-review.yml` or wait for Sunday schedule.
2. Inspect matrix jobs analyzing each daily log in parallel.
3. Verify consolidation step creates/updates `weekly-review/week-39.md` with:
   - Highlights, blockers, metrics, goal progress.
   - Token usage totals and API request IDs.
   - Links back to daily summaries.
4. Check that a PR `chore(weekly-review): week 39 insights` is opened with compliance checklist.

## Rollback & Failure Handling
- If sanitization fails: workflow exits with error referencing `ci/sanitizers/redact_personal_info.py`. Update rules and re-run job.
- If OpenAI API returns errors: job retries automatically up to 3 times; on final failure inspect warning artifact `ci/daily-reports/.../partial.md` and re-run step.
- If weekly PR is incorrect: close PR, delete generated report file, fix inputs, re-run workflow.

## Observability Checklist
- Daily artifacts appended to `.gitignore`? (Ensure not ignored — they must persist.)
- Inspect `ci/daily-reports/usage.csv` for token trends.
- Confirm repository retains sanitized excerpts and not raw sensitive data.
