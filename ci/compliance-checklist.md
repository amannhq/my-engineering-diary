# Compliance Checklist — Automated Weekly Insight Reviews

**Audit Date:** 2025-09-24
**Auditor:** Automation dry run (manual)

## Data Handling

- [x] Daily logs sanitized before LLM calls (`ci/sanitizers/redact_personal_info.py`).
- [x] Sanitization verified via unit tests (`tests/sanitizers/test_redact_personal_info.py`).
- [x] Personal identifiers replaced with `[REDACTED_*]` tokens.
- [x] LLM payloads stored only in `ci/daily-reports/` artifacts.

## Secrets & Credentials

- [x] `OPENAI_API_KEY` and `OPENAI_ORG` loaded from GitHub repository secrets.
- [x] `GH_TOKEN`/`GITHUB_TOKEN` required for PR automation (never written to disk).
- [x] No secrets committed to the repository (verified `.gitignore`).

## Artifact Retention

- [x] Daily artifacts retained for 14 days via `actions/upload-artifact`.
- [x] Weekly artifacts retained for 21 days.
- [x] Token usage appended to `ci/daily-reports/usage.csv` (Git tracked, no personal data).

## Transparency & Logging

- [x] All scripts emit structured JSON logs (`timestamp`, `event`, payload).
- [x] Weekly checklist stored in `weekly-review/week-XX-checklist.md` for PR review.
- [x] Manual test report recorded at `docs/manual-test-report.md`.

## Follow-Up Actions

- [ ] Execute workflows in GitHub Actions to capture real OpenAI runs once credentials available.
- [ ] Confirm shellcheck/ruff lint workflow passes on main branch.
