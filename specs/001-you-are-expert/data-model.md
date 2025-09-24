# Data Model: Automated Weekly Insight Reviews

## Entity Overview

### DailyLog
- **Primary Key**: `date` (ISO `YYYY-MM-DD`) + `weekday`
- **Attributes**:
  - `file_path`: relative path in `daily-logs/`
  - `goal_refs`: array of goal IDs (`G-YYYY-W##-NN`)
  - `summary`: short description of accomplishments
  - `blockers`: list of blockers
  - `created_at`: timestamp of log commit
  - `content_hash`: SHA256 for tamper detection
- **Relationships**:
  - 1-to-1 with `SanitizedExcerpt`
  - 1-to-many with `DailyInsight`

### SanitizedExcerpt
- **Primary Key**: `daily_log_id`
- **Attributes**:
  - `redacted_markdown`: sanitized Markdown sent to LLM
  - `redaction_rules_version`: identifier for rules in `ci/sanitizers/`
  - `generated_at`: CI timestamp
- **Relationships**:
  - Belongs to `DailyLog`
  - Source for `DailyInsight`

### DailyInsight
- **Primary Key**: `insight_id`
- **Attributes**:
  - `log_ref`: foreign key to `DailyLog`
  - `analysis_steps`: ordered array of step summaries
  - `status`: enum (`PASS`, `WARN`, `INFO`)
  - `token_usage`: struct {prompt, completion, total}
  - `api_request_id`: OpenAI Responses API identifier
  - `artifact_path`: location under `ci/daily-reports/YYYY-WW-DD/`
- **Relationships**:
  - References `SanitizedExcerpt`
  - Aggregated into `WeeklyReport`

### WeeklyReport
- **Primary Key**: `week_id` (`YYYY-W##`)
- **Attributes**:
  - `summary`: highlights, blockers, metrics
  - `goal_progress`: table keyed by goal ID
  - `token_usage_total`: aggregated token counts
  - `pr_number`: GitHub PR created for the report
  - `source_logs`: array of `DailyLog` references
  - `generated_at`: workflow timestamp
- **Relationships**:
  - 1-to-many with `DailyInsight`
  - Links to `Goal`

### Goal
- **Primary Key**: `goal_id` (`G-YYYY-W##-NN`)
- **Attributes**:
  - `title`
  - `description`
  - `success_metric`
  - `status`: enum (`Active`, `Completed`, `On Hold`)
  - `last_updated`: ISO timestamp
- **Relationships**:
  - Referenced by `DailyLog.goal_refs`
  - Aggregated in `WeeklyReport.goal_progress`

## State Transitions
- `DailyLog` → sanitized by CI → `SanitizedExcerpt`
- `SanitizedExcerpt` → analyzed via Responses API → `DailyInsight`
- Collection of `DailyInsight` (Mon–Sat) → synthesized → `WeeklyReport`

## Validation Rules
- Daily log filenames MUST match regex `^\d{4}-\d{2}-\d{2}\.[a-z]{3}\.log\.md$`.
- Every `DailyLog.goal_refs` entry MUST correspond to an existing `Goal`.
- Sanitization MUST run before any LLM analysis; redact personal information strings.
- Weekly reports MUST reference all contributing `DailyInsight.artifact_path` values.
- Token usage totals in `WeeklyReport` MUST equal the sum of contributing insights.

## Data Retention & Storage
- Markdown artifacts remain in git history; no external databases required.
- Sanitized excerpts stored under `ci/daily-reports/YYYY-WW-DD/` for traceability.
- Optional local cache for OpenAI responses cleared after weekly report generation.

## Scale Assumptions
- ≤7 daily logs per week; each log ≤5 KB.
- OpenAI parallel analysis matrix size limited to 7 jobs to respect rate limits.
- Weekly report size ≤3,000 tokens to keep PR diff manageable.
