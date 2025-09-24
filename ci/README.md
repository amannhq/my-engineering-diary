# CI Automation Overview

This directory contains all continuous integration and delivery assets that power the automated diary review pipeline. Use the sections below to run workflows manually, inspect generated artifacts, and understand how automated PRs are created.

## Structure
- `workflows/`: GitHub Actions workflows for daily validation and weekly synthesis.
- `prompts/`: Prompt templates and response schemas used with the OpenAI Responses API.
- `sanitizers/`: Pre-processing scripts that remove sensitive data before API calls.
- `scripts/`: Helper utilities invoked by workflows (payload prep, API clients, validation, reporting).
- `daily-reports/`: Generated artifacts per daily log (Markdown summaries, JSON event logs, token usage CSV).

## Running the Workflows

- **Daily validation:** Triggered on pushes that touch `daily-logs/**`. To run manually, open the GitHub Actions tab and dispatch `Daily Validation`, or execute `python -m ci.workflows.daily_validation --log-path <file> --artifact-dir ci/daily-reports/<tag>` locally (requires environment variables below).
- **Weekly review:** Scheduled via cron (`0 1 * * 0`) and manually invokable through the `Weekly Review` workflow. Running locally requires `OPENAI_API_KEY`, `OPENAI_ORG` (optional), and `GH_TOKEN` (to simulate PR creation via `gh`).

Each workflow prints structured JSON logs (`timestamp`, `event`, payload) to simplify troubleshooting in GitHub Actions.

## Artifacts & Reports

- **Daily run:** Stores `summary.md`, `events.json`, and updates `ci/daily-reports/usage.csv`. Artifacts are uploaded as `daily-validation-<run_id>` with 14-day retention.
- **Weekly run:** Writes consolidated events at `ci/daily-reports/<week-id>/`, generates `weekly-review/week-XX.md`, and produces a Constitution checklist `weekly-review/week-XX-checklist.md`. Artifacts upload under `weekly-review-<run_id>` with 21-day retention.

## PR Automation

The weekly workflow calls `ci/scripts/create_weekly_pr.sh`, which uses the GitHub CLI to create/update a PR titled `chore(weekly-review): week XX insights`. Ensure `GH_TOKEN` (or `GITHUB_TOKEN` with PR permissions) is available.

- Script arguments come from `ci/daily-reports/weekly-output.json`.
- Partial failures (e.g., missing `events.json`) are summarized in the PR body for follow-up.

## Troubleshooting

- **Goal validation failures:** Confirm `checks/goals/goals.md` exists and contains properly formatted IDs. Run `python -m ci.scripts.validate_goals` to see detailed JSON logs.
- **Missing artifacts:** Ensure `ci/daily-reports/` is not gitignored and workflows create directories before writing files.
- **PR creation errors:** Verify `gh` CLI is available in runners and `GH_TOKEN` has `pull_request:write` scope.
- **OpenAI API issues:** Check logs for `run_daily_analysis.api_response` events; the workflow stores raw `events.json` for debugging.

## Secrets & Environment Variables
Configure the following repository secrets in GitHub before running the workflows:

| Secret | Description |
| --- | --- |
| `OPENAI_API_KEY` | API key for the OpenAI Responses API. |
| `OPENAI_ORG` | Optional OpenAI organization identifier (if required by the account). |
| `GH_TOKEN` | Fine-grained token or default GITHUB_TOKEN with permissions to create PRs (used by weekly automation). |

The workflows also respect these optional variables:

- `RESPONSES_MODEL` (default `gpt-4.1`)
- `RESPONSES_TEMPERATURE` (default `0.2`)
- `DIARY_GOALS_FILE` (default `checks/goals/goals.md`)

Secrets are loaded at runtime by the GitHub Actions jobs; they must **never** be committed to the repository.
