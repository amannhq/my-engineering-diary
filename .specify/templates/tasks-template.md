# Tasks: [FEATURE NAME]
**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure, constitution gate outcomes
2. Load goal context from `checks/goals/goals.md`
   → If missing or malformed: ERROR "Goal alignment source unavailable"
3. Load optional design documents:
    → data-model.md: Extract entities → model tasks
    → contracts/: Each file → contract test task
    → research.md: Extract decisions → setup tasks
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
     → All automation tasks publish Markdown artifacts in `weekly-review/` or `ci/`
11. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions
- Reference supporting goal IDs and daily log evidence when relevant
- [ ] All contracts have corresponding tests
- [ ] All entities have model tasks
- [ ] All tests come before implementation
- [ ] Parallel tasks truly independent
- [ ] Each task specifies exact file path
- [ ] No task modifies same file as another [P] task
- [ ] Goal IDs referenced exist in `checks/goals/goals.md`
- [ ] Tasks generating reports output Markdown in `weekly-review/` or `ci/`
- [ ] Automation tasks document streaming requirements and prompt locations

---
**Based on Constitution v1.0.0 - See `/memory/constitution.md`**