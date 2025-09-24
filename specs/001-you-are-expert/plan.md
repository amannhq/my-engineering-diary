
# Implementation Plan: Automated Weekly Insight Reviews

**Branch**: `001-you-are-expert` | **Date**: 2025-09-24 | **Spec**: [`specs/001-you-are-expert/spec.md`](spec.md)
**Input**: Feature specification from `/specs/001-you-are-expert/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the current constitution (P1–P5, Operational Constraints, Workflow & Automation).
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Automate the diary workflow so that daily logs in `daily-logs/` feed into CI/CD pipelines which validate entries, run OpenAI Responses API analyses, and assemble weekly insight reports in Markdown. Implementation will create daily validation workflows, weekly aggregation jobs, LLM prompt/sanitizer assets, and Markdown PR outputs aligned with constitutional principles P1–P5.

## Technical Context
**Language/Version**: GitHub Actions YAML, Bash 5.x, optional Python 3.11 for scripting  
**Primary Dependencies**: OpenAI Responses API, `jq`, GitHub CLI, Markdown tooling  
**Storage**: Repository Markdown files (`daily-logs/`, `weekly-review/`, `ci/`)  
**Testing**: GitHub Actions workflow runs, unit tests for helper scripts via pytest (if Python scripts added)  
**Target Platform**: GitHub-hosted Ubuntu runners  
**Project Type**: Single repo automation pipeline  
**Performance Goals**: Daily workflow completes <10 min, weekly aggregation <15 min, API retries capped at 3 with exponential backoff  
**Constraints**: Must stream LLM steps to logs, sanitize personal info before API calls, no secrets committed  
**Scale/Scope**: Expect 7 daily logs per week, each <=5KB, weekly report with ≤3k tokens

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **P1 – Daily Log Fidelity**: Plan enforces filename linting and structure validation before invoking LLMs ➝ PASS.
- **P2 – Goal-Aligned Reflection**: Daily workflow loads `checks/goals/goals.md`, validates week-prefixed IDs, and fails fast if missing ➝ PASS with follow-up to seed goals file.
- **P3 – Automated Insight Pipeline**: Design introduces two workflows (daily, weekly) that automate LLM calls with retries and logging ➝ PASS.
- **P4 – Transparent LLM Execution**: Prompts/sanitizers stored under `ci/prompts/` and `ci/sanitizers/`, responses logged as Markdown + JSON ➝ PASS.
- **P5 – Markdown as Source of Truth**: Weekly report, daily artifacts, and PR templates written in Markdown referencing source logs ➝ PASS.
- **Operational Constraints**: Need to implement sanitization rules to redact personal info prior to API calls; must document token usage ➝ MITIGATED via preprocessing step and metrics logging.
- **Workflow & Automation**: Daily trigger on push to `daily-logs/`; weekly scheduled Sunday job; PR automation included ➝ PASS.

*No violations requiring Complexity Tracking.*

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Single project automation repository (Option 1). Add `ci/` directory for workflows, prompts, sanitizers, and reports.

## Phase 0: Outline & Research
1. **Unknowns & Dependencies**:
   - OpenAI Responses API usage patterns for streaming and step tracking.
   - Sanitization techniques for personal information prior to LLM calls.
   - GitHub Actions best practices for parallel matrix jobs and artifact uploads.
   - Goal file (`checks/goals/goals.md`) schema definition with `G-YYYY-W##-sequence` IDs.

2. **Research Tasks**:
   - `Research` Responses API streaming + tool outputs for weekly aggregation.
   - `Research` redaction pipelines (e.g., regex vs. structured scrubbing) for diaries.
   - `Research` GitHub Actions concurrency limits, caching, and security for secrets.
   - `Research` Markdown report templating for automated summaries.

3. **Consolidate Findings in `research.md`**:
   - Document chosen API endpoints, temperature settings, and response schema.
   - Record sanitization rules and storage location (`ci/sanitizers/` README).
   - Capture CI workflow structure, triggers, and failure handling strategies.
   - Define goal file table schema and maintenance cadence.

**Output**: `/specs/001-you-are-expert/research.md` summarizing decisions with rationale and alternatives.

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Data Model (`data-model.md`)**
   - Entities: DailyLog, Goal, DailyInsight, WeeklyReport, SanitizedExcerpt.
   - Capture fields (date, goals, content hash, tokens used, PR link) and relationships.
   - Define state transitions (e.g., Log → SanitizedExcerpt → Analyzed → Reported).

2. **Automation Contracts (`contracts/`)**
   - Document JSON schema for Responses API requests (prompt, input files, tool definitions).
   - Define expected response schema for daily analysis (steps, status, summary) and weekly synthesis.
   - Provide schema for CI artifacts (YAML/JSON) storing stream logs.

3. **Contract Tests**
   - Create Python or Bash validation scripts ensuring generated payloads match schema before API call.
   - Add failing tests verifying sanitization is applied and personal info is stripped.

4. **Integration Scenarios (`quickstart.md`)**
   - Outline manual verification steps: add sample daily log, run workflow, inspect outputs, confirm PR created.
   - Detail rollback steps if workflows fail mid-week.

5. **Agent Context**
   - Update via `.specify/scripts/bash/update-agent-context.sh windsurf` after documenting new tech (Responses API, sanitizers).

**Output**: `/specs/001-you-are-expert/data-model.md`, `/specs/001-you-are-expert/contracts/` schemas, failing contract tests, `/specs/001-you-are-expert/quickstart.md`, updated agent file.

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Base tasks on updated template emphasizing goal IDs and Markdown outputs.
- Derive setup tasks for creating `ci/` directories, prompt templates, sanitizers, and goal file seeding.
- For each contract/schema, create validation and failing test tasks.
- For each workflow (daily, weekly), create implementation and observability tasks.
- Include tasks for token usage logging, retry logic, and PR automation.

**Ordering Strategy**:
- Setup (directories, secrets scaffolding) → Tests (sanitization, schema validation) → Workflow implementation → Reporting/PR automation → Polish (docs, lint, monitoring).
- Mark [P] for tasks in distinct files (`ci/`, `weekly-review/`, `daily-logs/`).

**Estimated Output**: 30±5 tasks covering automation, testing, documentation, and governance compliance.

**IMPORTANT**: Execution deferred to `/tasks` workflow.

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented (not required)

---
**Based on Constitution v1.0.0 - See `/memory/constitution.md`**
