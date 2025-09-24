# Tasks: Automated Weekly Insight Reviews

**Input**: Design documents from `/specs/001-you-are-expert/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
1. Load plan.md from feature directory
   → Extract: tech stack, libraries, structure, constitution gate outcomes
2. Load goal context from `checks/goals/goals.md`
   → If missing or malformed: ERROR "Goal alignment source unavailable"
3. Load optional design documents:
    → data-model.md: Extract entities → model tasks
    → contracts/: Each file → contract test task
    → research.md: Extract decisions → setup tasks
    → quickstart.md: Extract verification scenarios
4. Scan relevant `daily-logs/YYYY-MM-DD.*.log.md` entries referenced in plan/spec
    → Collect evidence links for weekly review aggregation tasks
5. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
6. Apply task rules:
    → Different files = mark [P] for parallel
    → Same file = sequential (no [P])
    → Tests before implementation (TDD)
    → Include Markdown output tasks for weekly reports and daily validations where applicable
    → Ensure CI automation tasks stream intermediate steps in logs
7. Number tasks sequentially (T001, T002...)
8. Generate dependency graph
9. Create parallel execution examples
10. Validate task completeness:
    → All contracts have tests?
    → All entities have models?
    → All endpoints implemented?
    → All goal alignment references resolved?
11. Return: SUCCESS (tasks ready for execution)

## Task List

### Phase 3.1: Setup
- [x] **T001** Create `ci/` subdirectories (`ci/workflows/`, `ci/prompts/`, `ci/sanitizers/`, `ci/daily-reports/`) and add README stubs. (`/`)
- [x] **T002** Draft `checks/goals/goals.md` table with initial goals (`G-YYYY-W##-NN` format) and changelog section. (`checks/goals/goals.md`)
- [x] **T003 [P]** Document CI secrets requirements (`OPENAI_API_KEY`, `OPENAI_ORG`) in `ci/README.md` and reference GitHub settings. (`ci/README.md`)
- [x] **T004 [P]** Add `.github/SECURITY.md` note about LLM sanitization and data handling. (`.github/SECURITY.md`)

### Phase 3.2: Tests First (TDD)
- [x] **T005** Write failing schema validation test invoking `jsonschema` against `contracts/daily-analysis.schema.json`. (`tests/schema/test_daily_analysis.py`)
- [x] **T006 [P]** Write failing unit test for `ci/sanitizers/redact_personal_info.py` covering personal info redaction cases. (`tests/sanitizers/test_redact_personal_info.py`)
- [x] **T007 [P]** Add workflow contract test ensuring sanitization runs before Responses API invocation. (`tests/ci/test_sanitization_workflow.py`)
- [x] **T008 [P]** Create integration test harness script simulating Responses API call with fixture log and asserting step streaming log format. (`tests/integration/test_responses_stream.py`)
- [x] **T009 [P]** Draft failing test verifying weekly report generator links all daily artifacts and sums token usage correctly. (`tests/reports/test_weekly_aggregation.py`)

### Phase 3.3: Core Implementation
- [x] **T010** Implement `ci/sanitizers/redact_personal_info.py` to satisfy T006/T007. (`ci/sanitizers/redact_personal_info.py`)
- [x] **T011** Build helper script `ci/scripts/prepare_responses_payload.py` producing JSON matching `daily-analysis.schema.json`. (`ci/scripts/prepare_responses_payload.py`)
- [x] **T012** Implement Responses client wrapper `ci/scripts/run_responses_analysis.py` with streaming logging and retry logic. (`ci/scripts/run_responses_analysis.py`)
- [x] **T013** Configure GitHub Action `ci/workflows/daily-validation.yml` (push trigger on `daily-logs/**`) running sanitization, payload prep, Responses call per log (matrix). (`ci/workflows/daily-validation.yml`)
- [x] **T014** Configure GitHub Action `ci/workflows/weekly-review.yml` (cron Sunday) to aggregate daily artifacts, call synthesis prompt, update `weekly-review/week-XX.md`, and open PR. (`ci/workflows/weekly-review.yml`)
- [x] **T015** Implement prompt templates (`ci/prompts/daily-analysis.md`, `ci/prompts/weekly-synthesis.md`) capturing instructions, goal context, and output schema. (`ci/prompts/`)
- [x] **T016** Create token usage logger `ci/scripts/log_usage.py` invoked by workflows to append to `ci/daily-reports/usage.csv`. (`ci/scripts/log_usage.py`)
- [x] **T017** Implement goal file validator `ci/scripts/validate_goals.py` ensuring referenced IDs exist and follow format. (`ci/scripts/validate_goals.py`)

### Phase 3.4: Integration
- [x] **T018** Wire daily workflow to upload Markdown (`summary.md`) and JSON (`events.json`) artifacts per log; ensure retention policy. (`ci/workflows/daily-validation.yml`)
- [x] **T019 [P]** Integrate goal validator into both workflows, failing fast with actionable errors if missing IDs. (`ci/scripts/validate_goals.py` + workflows)
- [x] **T020 [P]** Add step to weekly workflow to collect partial failures and annotate PR checklist. (`ci/workflows/weekly-review.yml`)
- [x] **T021 [P]** Implement GitHub CLI script to create/update PR `chore(weekly-review): week XX insights` with checklist referencing constitution principles. (`ci/scripts/create_weekly_pr.sh`)
- [x] **T022 [P]** Add observability enhancements: structured logging (timestamps, log path) to all scripts and workflows. (`ci/scripts/` & `ci/workflows/`)

### Phase 3.5: Polish
- [x] **T023 [P]** Update `README.md` and `ci/README.md` with usage instructions, diagrams, and troubleshooting tips. (`README.md`, `ci/README.md`)
- **T024 [P]** Perform dry run using sample logs (per quickstart) and capture results in `docs/manual-test-report.md`. (`docs/manual-test-report.md`)
- **T025 [P]** Add linting/formatting configuration for Python/Bash scripts (`ruff`, `shellcheck`) via workflow updates. (`ci/workflows/lint.yml`)
- **T026 [P]** Review repository for sensitive data, confirm `.gitignore` permits storing artifacts, and document audit in `ci/compliance-checklist.md`. (`ci/compliance-checklist.md`)

## Dependencies
- **T005 → T010**: Schema validation must fail before implementation.
- **T006/T007 → T010**: Sanitizer tests drive implementation order.
- **T008/T009 → T012–T014**: Streaming and aggregation tests precede workflow builds.
- **T013 → T018**: Daily workflow must exist before artifact wiring.
- **T014 → T020–T021**: Weekly workflow needed before PR automation and annotations.
- **T015 → T012/T014**: Prompt templates required before Responses client and weekly synthesis.
- **T016 → T014**: Token logger integrated into weekly workflow after implementation.
- **T017 → T019**: Goal validator written before integration into workflows.
- **T018–T022 → T024**: Integration tasks complete before manual dry run.

## Parallel Execution Examples
- **Example 1**: After setup (T001–T004), run T005, T006 [P], T007 [P], T008 [P], T009 [P] concurrently via separate test commands.
- **Example 2**: Once workflows exist (T013–T014), execute T019 [P], T020 [P], T021 [P], T022 [P] in parallel—they touch distinct scripts/steps.
- **Example 3**: During polish, T023 [P], T025 [P], T026 [P] can run together; keep T024 sequential to validate consolidated outputs.

---
**Based on Constitution v1.0.0 - See `/memory/constitution.md`**
