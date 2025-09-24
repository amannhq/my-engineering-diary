# Research: Automated Weekly Insight Reviews

## OpenAI Responses API Streaming
- **Decision**: Use the Responses API with `gpt-4.1` and `reasoning: { effort: "medium" }` to enable step-wise analysis and streaming logs.
- **Rationale**: Provides structured tool outputs and streaming events required for constitutional transparency.
- **Alternatives Considered**:
  - **Responses API without streaming**: Rejected; violates P3/P4 requirements for step traceability.
  - **Assistants API**: Heavier state management, less direct streaming control.

## Sanitization Strategy
- **Decision**: Implement pre-processing Bash/Python script under `ci/sanitizers/redact_personal_info.py` to remove personal names, emails, and free-form notes flagged as sensitive.
- **Rationale**: Constitution Operational Constraints demand personal information redaction before external API calls.
- **Alternatives Considered**:
  - Manual log redaction: Error prone, non-scalable.
  - Rely solely on OpenAI response filters: Insufficient guarantees, no repository traceability.

## GitHub Actions Architecture
- **Decision**: Create two workflows: `ci/daily-validation.yml` (push trigger on `daily-logs/**`) and `ci/weekly-review.yml` (cron `0 1 * * 0`). Utilize matrix strategy to analyze each log in parallel with a reusable `analyze-log` job.
- **Rationale**: Aligns with requirement for daily checks and Sunday aggregation while keeping runs observable.
- **Alternatives Considered**:
  - Single workflow with conditional logic: Reduces clarity, complicates scheduling and streaming logs.
  - Local scripts triggered manually: Violates automation requirement (P3).

## Goal File Schema
- **Decision**: Maintain `checks/goals/goals.md` table with columns: `Goal ID`, `Title`, `Description`, `Success Metric`, `Status`, `Last Updated`. IDs follow `G-YYYY-W##-NN` format.
- **Rationale**: Supports automated validation and historical auditing per clarification.
- **Alternatives Considered**:
  - JSON/YAML format: Harder for manual edits/review; Markdown aligns with P5.

## Token Usage & Cost Tracking
- **Decision**: Capture OpenAI usage metadata from Responses API (tokens, request ID) and append to weekly report plus `ci/daily-reports/usage.csv`.
- **Rationale**: Supports Goal G005 (Cost & Usage Awareness) and provides audit trail.
- **Alternatives Considered**:
  - Ignoring token metrics: Would violate requirement FR-007 and reduce cost oversight.

## Failure Handling & Retries
- **Decision**: For each LLM call, implement exponential backoff (`1s, 4s, 9s`) with max 3 retries; on final failure, write partial artifact and continue weekly job with warning.
- **Rationale**: Ensures pipelines do not halt due to transient issues while preserving transparency.
- **Alternatives Considered**:
  - Hard failure on first error: Conflicts with requirement to keep pipelines non-blocking for insight quality.
  - Unlimited retries: Risk of runaway costs and timeouts.

## Observability & Artifact Storage
- **Decision**: Store daily analysis outputs in `ci/daily-reports/YYYY-WW-DD/` with both Markdown summary and JSON event log; weekly report references these artifacts.
- **Rationale**: Meets P4/P5 for auditable records and Markdown trace-ability.
- **Alternatives Considered**:
  - Centralized database/logging: Overkill for Markdown-based workflow, increases maintenance burden.
