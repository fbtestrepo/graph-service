# Tasks: Deploy-Scope Graph Resolution Fix

**Input**: Design documents from /specs/015-fix-deploy-scope-graph/
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/http-api.md, quickstart.md

**Tests**: Tests are required for this feature because the specification and user request explicitly require coverage of the C and E3 scenarios plus a full-suite no-regression run.

**Organization**: Tasks are grouped by user story to keep each story independently implementable and testable.

## Phase 1: Setup (Scope Lock-In)

**Purpose**: Confirm behavior-only scope and implementation boundaries before editing code.

- [X] T001 Review required behavior deltas and ordering/error constraints in specs/015-fix-deploy-scope-graph/spec.md and specs/015-fix-deploy-scope-graph/contracts/http-api.md
- [X] T002 [P] Confirm implementation scope is limited to src/core/domain/micro_affinity_group_deployment_graph.py and src/core/use_cases/get_micro_affinity_group_deployment_scope.py using specs/015-fix-deploy-scope-graph/plan.md
- [X] T003 [P] Prepare regression execution checklist in specs/015-fix-deploy-scope-graph/quickstart.md for targeted and full-suite test runs

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared traversal and orchestration seams required by all user stories.

**⚠️ CRITICAL**: No user story implementation starts before this phase is complete.

- [X] T004 Refactor traversal seed and branch-path helper seams in src/core/domain/micro_affinity_group_deployment_graph.py for one-hop-upstream seeding and root fallback behavior
- [X] T005 Refactor deployment-scope orchestration interfaces to consume traversal seed/path metadata in src/core/use_cases/get_micro_affinity_group_deployment_scope.py
- [X] T006 [P] Add/update shared regression fixtures for reported graph shapes in tests/test_micro_affinity_group_deployment_scope_use_case.py

**Checkpoint**: Shared graph traversal and orchestration seams are ready.

---

## Phase 3: User Story 1 - Resolve Full Scope From One-Hop Upstream Seeds (Priority: P1) 🎯 MVP

**Goal**: Ensure downstream graph closure starts from immediate one-hop upstream dependents and includes complete expected edges.

**Independent Test**: Call deploy-scope for roots C and E3 and verify one-hop-upstream-seeded downstream coverage in use-case, endpoint, and persistence tests.

### Tests for User Story 1

- [X] T007 [P] [US1] Add use-case regression assertions for complete one-hop-upstream-seeded downstream edge inclusion in tests/test_micro_affinity_group_deployment_scope_use_case.py
- [X] T008 [P] [US1] Add endpoint regression assertions for complete one-hop-upstream-seeded downstream edge inclusion in tests/test_micro_affinity_group_deployment_scope_endpoint.py
- [X] T009 [P] [US1] Add persistence-backed regression assertions for complete one-hop-upstream-seeded downstream edge inclusion in tests/test_micro_affinity_group_deployment_scope_persistence.py
- [X] T009a [P] [US1] Add traversal-boundary regression assertions verifying inclusion through hop 30 and exclusion from hop 31 onward in tests/test_micro_affinity_group_deployment_scope_use_case.py
- [X] T009b [P] [US1] Add traversal-boundary regression assertions verifying inclusion through hop 30 and exclusion from hop 31 onward in tests/test_micro_affinity_group_deployment_scope_endpoint.py
- [X] T009c [P] [US1] Add traversal-boundary regression assertions verifying inclusion through hop 30 and exclusion from hop 31 onward in tests/test_micro_affinity_group_deployment_scope_persistence.py

### Implementation for User Story 1

- [X] T010 [US1] Implement one-hop-upstream seed discovery with root fallback traversal start in src/core/domain/micro_affinity_group_deployment_graph.py
- [X] T011 [US1] Integrate updated traversal start-set behavior into deploy-scope response assembly in src/core/use_cases/get_micro_affinity_group_deployment_scope.py

**Checkpoint**: US1 produces complete seeded downstream graph coverage for C and E3 scenarios.

---

## Phase 4: User Story 2 - Mark Only Path Back-Edges As Cyclic (Priority: P2)

**Goal**: Classify cycles strictly as path back-edges and bypass only those edges.

**Independent Test**: Verify cycle-edge identification for C and E3 at use-case, endpoint, and persistence layers and ensure non-back-edges are not flagged.

### Tests for User Story 2

- [X] T012 [P] [US2] Add use-case assertions that only path back-edges are marked cyclic and mirrored to bypassed_edges in tests/test_micro_affinity_group_deployment_scope_use_case.py
- [X] T013 [P] [US2] Add endpoint assertions that only path back-edges are marked cyclic and mirrored to bypassed_edges in tests/test_micro_affinity_group_deployment_scope_endpoint.py
- [X] T014 [P] [US2] Add persistence assertions that only path back-edges are marked cyclic and mirrored to bypassed_edges in tests/test_micro_affinity_group_deployment_scope_persistence.py

### Implementation for User Story 2

- [X] T015 [US2] Implement path-scoped back-edge cycle detection using branch-local visited path initialization (root plus immediate upstream dependents) in src/core/domain/micro_affinity_group_deployment_graph.py
- [X] T016 [US2] Propagate cyclic-edge flags and bypassed-edge outputs without changing response schema in src/core/use_cases/get_micro_affinity_group_deployment_scope.py

**Checkpoint**: US2 marks only true path back-edges and bypasses only those edges.

---

## Phase 5: User Story 3 - Keep Deployment Steps Valid After Cycle Bypass (Priority: P3)

**Goal**: Preserve topological step logic while excluding only bypassed cyclic edges, keep deterministic ordering, and avoid acyclic regressions.

**Independent Test**: Validate expected deployment steps for C and E3, deterministic ordering rules, preserved 404 versus 422 semantics, and unchanged acyclic behaviors.

### Tests for User Story 3

- [X] T017 [P] [US3] Add use-case regression assertions for reduced-graph deployment steps, deterministic ordering, explicit graph_has_cycles true and false behavior, explicit no-upstream-dependent root fallback behavior, and acyclic non-regression in tests/test_micro_affinity_group_deployment_scope_use_case.py
- [X] T018 [P] [US3] Add endpoint regression assertions for reduced-graph deployment steps, deterministic ordering, explicit graph_has_cycles true and false behavior, explicit no-upstream-dependent root fallback behavior, and 404 versus 422 semantics in tests/test_micro_affinity_group_deployment_scope_endpoint.py
- [X] T019 [P] [US3] Add persistence regression assertions for reduced-graph deployment steps, deterministic ordering, explicit graph_has_cycles true and false behavior, explicit no-upstream-dependent root fallback behavior, and acyclic non-regression in tests/test_micro_affinity_group_deployment_scope_persistence.py

### Implementation for User Story 3

- [X] T020 [US3] Update reduced-graph step calculation to exclude only bypassed cyclic edges while preserving existing topological layering behavior in src/core/domain/micro_affinity_group_deployment_graph.py
- [X] T021 [US3] Enforce deterministic response ordering contract (non-cyclic edges then cyclic edges, sorted lexicographically; sorted step members) in src/core/use_cases/get_micro_affinity_group_deployment_scope.py
- [X] T022 [US3] Refactor traversal/cycle code to remove scenario-specific hardcoded behavior and keep modular helper boundaries in src/core/domain/micro_affinity_group_deployment_graph.py and src/core/use_cases/get_micro_affinity_group_deployment_scope.py

**Checkpoint**: US3 returns correct steps/order/error semantics and preserves acyclic behavior.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and documentation updates across all stories.

- [X] T023 Run targeted deploy-scope suites from specs/015-fix-deploy-scope-graph/quickstart.md against tests/test_micro_affinity_group_deployment_scope_use_case.py, tests/test_micro_affinity_group_deployment_scope_endpoint.py, and tests/test_micro_affinity_group_deployment_scope_persistence.py
- [X] T024 Run focused 404/422 semantic regression command from specs/015-fix-deploy-scope-graph/quickstart.md against tests/test_micro_affinity_group_deployment_scope_endpoint.py
- [X] T025 Run architecture guard using check_core_purity.py
- [X] T026 Run full regression suite command from specs/015-fix-deploy-scope-graph/quickstart.md against tests/
- [X] T027 Update verified execution notes and outcomes in specs/015-fix-deploy-scope-graph/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): no dependencies.
- Foundational (Phase 2): depends on Setup completion and blocks all user stories.
- User Story phases (Phase 3 onward): depend on Foundational completion.
- Polish (Phase 6): depends on completion of selected user stories.

### User Story Dependencies

- US1 (P1): starts after Foundational and is the MVP slice.
- US2 (P2): can start after Foundational; may reuse US1 fixtures but remains independently testable.
- US3 (P3): can start after Foundational; may reuse US1/US2 fixtures but remains independently testable.

### Within Each User Story

- Write story tests first and confirm they fail before implementation updates.
- Update pure core graph logic before use-case orchestration changes.
- Validate each story checkpoint before proceeding to the next selected story in the delivery plan.

### Parallel Opportunities

- Phase 1: T002 and T003 can run in parallel.
- Phase 2: T006 can run in parallel with T004/T005 after scope lock-in.
- US1: T007, T008, T009, T009a, T009b, and T009c can run in parallel.
- US2: T012, T013, and T014 can run in parallel.
- US3: T017, T018, and T019 can run in parallel.

---

## Parallel Example: User Story 1

```bash
Task: "Add use-case regression assertions for complete one-hop-upstream-seeded downstream edge inclusion in tests/test_micro_affinity_group_deployment_scope_use_case.py"
Task: "Add endpoint regression assertions for complete one-hop-upstream-seeded downstream edge inclusion in tests/test_micro_affinity_group_deployment_scope_endpoint.py"
Task: "Add persistence-backed regression assertions for complete one-hop-upstream-seeded downstream edge inclusion in tests/test_micro_affinity_group_deployment_scope_persistence.py"
Task: "Add traversal-boundary regression assertions verifying inclusion through hop 30 and exclusion from hop 31 onward in tests/test_micro_affinity_group_deployment_scope_use_case.py"
Task: "Add traversal-boundary regression assertions verifying inclusion through hop 30 and exclusion from hop 31 onward in tests/test_micro_affinity_group_deployment_scope_endpoint.py"
Task: "Add traversal-boundary regression assertions verifying inclusion through hop 30 and exclusion from hop 31 onward in tests/test_micro_affinity_group_deployment_scope_persistence.py"
```

---

## Parallel Example: User Story 2

```bash
Task: "Add use-case assertions that only path back-edges are marked cyclic and mirrored to bypassed_edges in tests/test_micro_affinity_group_deployment_scope_use_case.py"
Task: "Add endpoint assertions that only path back-edges are marked cyclic and mirrored to bypassed_edges in tests/test_micro_affinity_group_deployment_scope_endpoint.py"
Task: "Add persistence assertions that only path back-edges are marked cyclic and mirrored to bypassed_edges in tests/test_micro_affinity_group_deployment_scope_persistence.py"
```

---

## Parallel Example: User Story 3

```bash
Task: "Add use-case regression assertions for reduced-graph deployment steps, deterministic ordering, explicit graph_has_cycles true and false behavior, explicit no-upstream-dependent root fallback behavior, and acyclic non-regression in tests/test_micro_affinity_group_deployment_scope_use_case.py"
Task: "Add endpoint regression assertions for reduced-graph deployment steps, deterministic ordering, explicit graph_has_cycles true and false behavior, explicit no-upstream-dependent root fallback behavior, and 404 versus 422 semantics in tests/test_micro_affinity_group_deployment_scope_endpoint.py"
Task: "Add persistence regression assertions for reduced-graph deployment steps, deterministic ordering, explicit graph_has_cycles true and false behavior, explicit no-upstream-dependent root fallback behavior, and acyclic non-regression in tests/test_micro_affinity_group_deployment_scope_persistence.py"
```

---

## Implementation Strategy

### MVP First (US1 only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate C and E3 seeded downstream edge coverage independently.
4. Demo MVP behavior fix before cycle and step refinements.

### Incremental Delivery

1. Deliver US1 graph completeness.
2. Deliver US2 cycle-edge correctness.
3. Deliver US3 deployment-step correctness and deterministic ordering.
4. Run cross-cutting polish validation and full-suite regression.

### Parallel Team Strategy

1. One developer handles core traversal/cycle implementation tasks in src/core/domain/micro_affinity_group_deployment_graph.py.
2. One developer handles orchestration/response assembly tasks in src/core/use_cases/get_micro_affinity_group_deployment_scope.py.
3. One developer handles parallel test coverage tasks across the three deployment-scope test modules.

---

## Notes

- [P] marks tasks that can execute in parallel because they touch independent files.
- Every task includes concrete repository paths for direct execution.
- Suggested MVP scope is User Story 1.
- Keep code modular and avoid hardcoding sample-specific constants to satisfy review constraints.
