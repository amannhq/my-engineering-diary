<!--
Sync Impact Report
- Version change: 0.0.0 → 1.0.0
- Modified principles: N/A (initial ratification)
- Added sections: Core Principles; Operational Constraints; Workflow & Automation; Governance
- Templates requiring updates:
  - ⚠ pending `.specify/templates/plan-template.md`
  - ⚠ pending `.specify/templates/spec-template.md`
  - ⚠ pending `.specify/templates/tasks-template.md`
- Follow-up TODOs: None
-->

# My Engineering Diary Constitution

## Core Principles

### P1. Daily Log Fidelity
- **Directive**: Every working day with activity MUST produce a markdown log file in `daily-logs/` named using the ISO date plus weekday suffix (e.g., `2025-09-24.wed.log.md`) and committed before that day's closing reflection.
- **Scope**: Logs MUST capture objectives, steps taken, blockers, and outcomes in Markdown tables or bullet lists for machine readability.
- **Rationale**: Consistent, structured daily evidence enables reliable automated synthesis and prevents gaps during weekly reviews.

### P2. Goal-Aligned Reflection
- **Directive**: Daily reflections MUST reference the active goals defined in `checks/goals/goals.md`, explicitly mapping actions and learnings to goal identifiers.
- **Scope**: When goals change, the update MUST precede the next daily log, and historical logs remain immutable; adjustments are documented through addendum sections.
- **Rationale**: Tying work to declared goals keeps the automation grounded in the user's strategic intent and surfaces drift early.

### P3. Automated Insight Pipeline
- **Directive**: CI/CD workflows MUST orchestrate daily validation and weekly aggregation jobs without manual intervention, relying on version-controlled configuration.
- **Scope**: The pipeline MUST use the OpenAI Responses API (or compatible equivalent) for analysis, handle retries idempotently, and stream intermediate step statuses to CI logs without failing the pipeline for content-based findings.
- **Rationale**: A deterministic automation backbone ensures that insights are reproducible, auditable, and scalable as the diary evolves.

### P4. Transparent LLM Execution
- **Directive**: All LLM prompts, response schemas, and evaluation criteria MUST live in the repository under `ci/` or `checks/` so reviewers can trace decision-making.
- **Scope**: Each automated step MUST emit structured YAML or JSON summaries alongside human-readable Markdown to enable downstream tooling and manual audits.
- **Rationale**: Visibility into automated reasoning preserves trust, supports debugging, and enables future model swaps without regressions.

### P5. Markdown as Source of Truth
- **Directive**: Weekly reviews, automation reports, and generated pull requests MUST be written in Markdown, referencing source commits and extracted insights.
- **Scope**: Generated reports MUST include sections for highlights, blockers, metrics, and goal progress, with links back to the contributing daily logs.
- **Rationale**: Markdown keeps the knowledge base lightweight, reviewable, and friendly to CI diffing while remaining portable across tooling.

## Operational Constraints
- **OpenAI Integration**: Workflows MUST authenticate via environment-provided API keys; keys are never committed. Prompt templates live under `ci/prompts/` with clear version tags.
- **Streaming Requirements**: CI jobs MUST stream each analysis step to logs in chronological order, including timestamps and the originating log file path.
- **Data Residency**: Only daily log excerpts and goal references are sent to external APIs; redactions for sensitive content MUST occur via preprocessors stored under `ci/sanitizers/`.
- **Artifact Storage**: Automation outputs (per-day analyses, weekly synthesis, PR summaries) MUST be stored in `weekly-review/` with filenames `week-XX.md` and appended rather than overwritten.

## Workflow & Automation
- **Daily Validation**:
  - Trigger: Any push containing files in `daily-logs/`.
  - Steps: filename convention check → goal reference lint → LLM reflection check (non-blocking) → status summary artifact.
  - Outputs: `ci/daily-reports/YYYY-WW-DD.md` containing pass/fail with rationale.
- **Weekly Review (Sunday cadence)**:
  - Aggregates Monday–Saturday logs (inclusive) based on ISO week.
  - Runs parallel LLM analyses per log, streams progress, then consolidates with a second model call into `weekly-review/week-XX.md` and opens a PR titled `chore(weekly-review): week XX insights`.
  - PR MUST include checklist confirming adherence to Principles P1–P5.
- **Goal Checks**: Prior to analysis, the pipeline loads `checks/goals/goals.md`; missing or malformed file causes a failing gate with actionable error text.

## Governance
- **Authority**: This constitution supersedes prior workflow notes for the diary automation. Any exceptions require explicit approval documented in PR descriptions.
- **Amendments**: Proposals are submitted via PR modifying this file; reviewers confirm impact across templates and automation scripts. Adoption occurs upon merge, with `Last Amended` updated to the merge date.
- **Versioning Policy**: Use semantic versioning. Major = redefined principles or removal; Minor = new principles or sections; Patch = clarifications.
- **Compliance Review**: CI reviewers MUST verify daily and weekly workflow updates against Principles P1–P5. Quarterly audits ensure prompt templates and sanitizers match declared constraints.

**Version**: 1.0.0 | **Ratified**: 2025-09-24 | **Last Amended**: 2025-09-24