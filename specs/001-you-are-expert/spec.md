# Feature Specification: Automated Weekly Insight Reviews

**Feature Branch**: `001-you-are-expert`  
**Created**: 2025-09-24  
**Status**: Draft  
**Input**: User description: "You are expert at writing and reviews of a person weekly insights ... Use the open ai responses api for this search the web for the docs."

## Execution Flow (main)
1. Establish structured daily logging standards and goal references to ensure every workday produces a compliant Markdown entry in `daily-logs/`.
2. Implement daily CI validation that triggers on pushes touching `daily-logs/`, streaming LLM-assisted reflections while never blocking merges on insight quality alone.
3. Aggregate Monday–Saturday logs each Sunday via a scheduled workflow that runs LLM analyses in parallel using the OpenAI Responses API, emitting step-by-step status updates to CI logs.
4. Consolidate daily findings into a weekly Markdown report in `weekly-review/week-XX.md`, generate an accompanying pull request, and attach the automated checklist for constitutional compliance.
5. Persist artifacts (per-day analyses, sanitized payloads, prompt templates) in version control to maintain transparency and auditability.

## ⚡ Quick Guidelines
- ✅ Keep all artifacts in Markdown with tables/sections optimized for LLM parsing.
- ✅ Stream intermediate automation steps for observability and debugging.
- ✅ Authenticate OpenAI access via environment variables managed in CI secrets.
- ❌ Never commit API keys or raw sensitive diary content; use sanitizers before LLM calls.
- ❌ Do not bypass goal alignment checks; update `checks/goals/goals.md` before logging against new objectives.

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a diarist, I want every week of daily reflections to culminate in an automated insight report so that I can track progress toward my goals without manual collation.

### Acceptance Scenarios
1. **Given** compliant daily logs for Monday–Saturday, **When** the Sunday workflow runs, **Then** a new `weekly-review/week-XX.md` file is generated with highlights, blockers, metrics, and goal progress referencing each contributing log.
2. **Given** a push containing new daily log files, **When** the daily validation workflow executes, **Then** CI logs display a streamed breakdown of LLM evaluation steps and produce a status artifact in `ci/daily-reports/YYYY-WW-DD.md` without failing the pipeline for subjective feedback.
3. **Given** goals recorded in `checks/goals/goals.md`, **When** a daily log references a goal ID, **Then** both daily and weekly automation confirm the goal exists and include it in the generated reports.

### Edge Cases
- Missing or improperly named logs trigger a failing gate with actionable remediation instructions and the workflow stops before LLM calls.
- Redacted days (e.g., personal leave) are explicitly labeled and excluded from weekly synthesis without causing pipeline failures.
- API rate limits or OpenAI downtime trigger exponential backoff with a retry cap; upon exhaustion, automation records a partial result and surfaces a warning in the PR checklist.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST enforce daily log filenames in the format `YYYY-MM-DD.<dow>.log.md` and validate structure (title, goals table, steps, outcomes). *(Goal: G001)*
- **FR-002**: CI/CD MUST trigger on any change under `daily-logs/` and run non-blocking LLM reflection checks, streaming progress to logs. *(Goal: G002)*
- **FR-003**: Weekly scheduled workflow MUST aggregate Monday–Saturday logs, execute per-log analyses in parallel via the OpenAI Responses API, and persist individual summaries as Markdown artifacts. *(Goals: G002, G003)*
- **FR-004**: Weekly consolidation MUST produce `weekly-review/week-XX.md` with highlights, blockers, metrics, goal alignment, and links to source logs, then open a PR `chore(weekly-review): week XX insights`. *(Goals: G001, G003)*
- **FR-005**: Automation MUST reference prompts and sanitizers stored under `ci/prompts/` and `ci/sanitizers/`, ensuring no raw secrets or sensitive data leave the repo. *(Goal: G004)*
- **FR-006**: Pipeline MUST fail fast when `checks/goals/goals.md` is missing, malformed, or lacks referenced goal IDs, emitting a corrective message. *(Goal: G001)*
- **FR-007**: All CI jobs MUST authenticate to OpenAI via environment-based secrets and log token usage metrics in the weekly report. *(Goal: G005)*

### Key Entities *(include if feature involves data)*
- **Daily Log Entry**: Structured Markdown file capturing date metadata, goal references, actions, blockers, and outcomes.
- **Goal Definition**: Markdown table within `checks/goals/goals.md` containing goal IDs, titles, descriptions, and success metrics.
- **Daily Insight Artifact**: Machine-generated Markdown or YAML summarizing LLM evaluation results stored under `ci/daily-reports/`.
- **Weekly Review Report**: Markdown document under `weekly-review/` compiling insights, metrics, and next steps for the week.
- **Automation Checklist**: Structured data (YAML/JSON) attached to weekly PR verifying compliance with Core Principles P1–P5.

## Goal Alignment *(mandatory)*

- **Primary Goals Supported**: 
  - G001 Daily Log Fidelity — Maintain consistent, compliant daily entries. *(New goal to add to `checks/goals/goals.md`.)*
  - G002 LLM-Assisted Daily Reflection — Capture actionable automated feedback per log.
  - G003 Weekly Synthesis Automation — Deliver consistent weekly insight reports.
  - G004 Transparency & Safety — Keep prompts/sanitizers versioned and enforce redaction.
  - G005 Cost & Usage Awareness — Track API consumption for sustainability.
- **Daily Log References**: `daily-logs/YYYY-MM-DD.<dow>.log.md` entries serve as primary evidence for daily progress and must cite goal IDs in front-matter tables.
- **Adjustments Needed**: Seed `checks/goals/goals.md` with the goals above; introduce a changelog section to track goal revisions.

## Clarifications

### Session 2025-09-24
- **Goal ID convention?** → Use week-prefixed identifiers in the form `G-YYYY-W##-sequence` (Option B).
- **Sanitization scope?** → Redact personal information before OpenAI calls; document/update rules alongside sanitizers.

## Open Questions

- None at this time.

## Review & Acceptance Checklist
### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous  
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified
- [ ] Goal alignment section references valid goal IDs *(Requires creation of the goals file with listed IDs)*
- [ ] All supporting evidence paths point to Markdown logs *(Dependent on daily log samples)*
- [x] Outputs maintain Markdown structure with traceable links

## Execution Status
- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed
- [x] Goal alignment captured

---
**Based on Constitution v1.0.0 - See `/memory/constitution.md`**

---
