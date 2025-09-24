# Automated Weekly Insight Reviews

This repository hosts the automation that turns daily markdown diary entries into weekly insight reports. GitHub Actions workflows sanitize logs, invoke the OpenAI Responses API, aggregate results, and open a weekly pull request summarizing progress against goals.

## Repository Layout

- `daily-logs/` — Source markdown diary entries (`YYYY-MM-DD.<dow>.log.md`).
- `weekly-review/` — Generated weekly reports (`week-XX.md`) and Constitution checklists.
- `ci/` — Automation assets (workflows, scripts, prompts, sanitizers, generated artifacts).
- `specs/` — Feature planning documents (`plan.md`, `tasks.md`, contracts, research, quickstart).
- `tests/` — Pytest suites covering sanitizers, schema validation, integration harnesses, and weekly aggregation.

## Quickstart

1. Create daily logs following `YYYY-MM-DD.<dow>.log.md` naming and reference goal IDs (`G-YYYY-W##-NN`).
2. Configure repository secrets (`OPENAI_API_KEY`, `OPENAI_ORG`, `GH_TOKEN`).
3. Push diary changes to trigger the daily validation workflow.
4. Review generated artifacts under `ci/daily-reports/<week-tag>/`.
5. Let the scheduled weekly workflow assemble the Sunday report and PR, or dispatch it manually from GitHub Actions.

## Local Testing

- Run sanitizer unit tests: `pytest tests/sanitizers/test_redact_personal_info.py`.
- Validate schema payloads: `pytest tests/schema/test_daily_analysis.py`.
- Execute the daily workflow script locally: `python -m ci.workflows.daily_validation --log-path daily-logs/<file> --artifact-dir ci/daily-reports/<tag>` (requires OpenAI credentials).

## Observability & Compliance

- All scripts emit structured JSON log lines (`timestamp`, `event`, metadata) for GitHub Actions logs.
- Personal information is redacted before API calls (`ci/sanitizers/redact_personal_info.py`).
- Token usage is appended to `ci/daily-reports/usage.csv` for cost tracking.

## Further Reading

- `ci/README.md` — Workflow operations, artifacts, troubleshooting, PR automation.
- `specs/001-you-are-expert/plan.md` — Technical plan and architectural decisions.
- `specs/001-you-are-expert/tasks.md` — Task breakdown and execution checklist.
