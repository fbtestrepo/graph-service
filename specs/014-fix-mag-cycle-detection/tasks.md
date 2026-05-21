# Tasks: Fix MAG Cycle Detection

**Input**: Design documents from `/specs/014-fix-mag-cycle-detection/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are required for this feature because the specification explicitly requires automated regression coverage for the reported cyclic graph, preservation of acyclic behavior, and a full-suite no-regression pass.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Execution Scope Lock-In)

**Purpose**: Confirm the behavior-only scope and keep implementation constrained to the existing deployment-scope surfaces.

- [X] T001 Review the corrected endpoint behavior and expected stage output in `specs/014-fix-mag-cycle-detection/contracts/http-api.md` and `specs/014-fix-mag-cycle-detection/quickstart.md`
- [X] T002 [P] Confirm the implementation stays limited to `src/core/domain/micro_affinity_group_deployment_graph.py` and `src/core/use_cases/get_micro_affinity_group_deployment_scope.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prepare the shared graph-reduction and use-case orchestration surfaces that all user stories depend on.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T003 [P] Introduce traversal-path-aware graph helper seams for cycle-edge selection and reduced-graph stage calculation in `src/core/domain/micro_affinity_group_deployment_graph.py`
- [X] T004 [P] Refactor deployment-scope orchestration to consume path-scoped cycle metadata without changing the response shape in `src/core/use_cases/get_micro_affinity_group_deployment_scope.py`

**Checkpoint**: Shared cycle-detection and stage-calculation seams are ready for story-level implementation.

---

## Phase 3: User Story 1 - Mark The Correct Back-Edge (Priority: P1) 🎯 MVP

**Goal**: Mark only the true path-scoped back-edge for the reported cyclic graph rooted at `C`.

**Independent Test**: Seed the reported graph and verify at use-case, persistence, and endpoint levels that `E1 -> C` is the only edge flagged as cyclic, `C -> D` remains non-cyclic, and the immediate upstream consumer edges `A -> C` and `B -> C` remain included and non-cyclic.

### Tests for User Story 1

- [X] T005 [P] [US1] Add reported-graph back-edge regression coverage in `tests/test_micro_affinity_group_deployment_scope_use_case.py`
- [X] T006 [P] [US1] Add reported-graph API regression asserting only `E1 -> C` is cyclic in `tests/test_micro_affinity_group_deployment_scope_endpoint.py`
- [X] T007 [P] [US1] Add persistence-backed regression data and assertions for cyclic-edge selection in `tests/test_micro_affinity_group_deployment_scope_persistence.py`
- [X] T007a [P] [US1] Add explicit assertions that immediate upstream consumer edges `A -> C` and `B -> C` remain present and non-cyclic in `tests/test_micro_affinity_group_deployment_scope_use_case.py` and `tests/test_micro_affinity_group_deployment_scope_endpoint.py`
- [X] T007b [P] [US1] Add a second cyclic regression with an alternate branch or multi-path graph to verify that only edges pointing back to nodes on the current active traversal path are marked cyclic in `tests/test_micro_affinity_group_deployment_scope_use_case.py`

### Implementation for User Story 1

- [X] T008 [US1] Implement path-scoped back-edge detection instead of global SCC edge selection in `src/core/domain/micro_affinity_group_deployment_graph.py`
- [X] T009 [US1] Update deployment-scope graph assembly to mark only path-scoped cyclic edges in `src/core/use_cases/get_micro_affinity_group_deployment_scope.py`

**Checkpoint**: The response exposes the correct cyclic edge for the reported graph without changing the public contract.

---

## Phase 4: User Story 2 - Produce Correct Deployment Stages After Cycle Removal (Priority: P2)

**Goal**: Recompute deployment stages from the graph reduced by excluding only the true cyclic back-edge.

**Independent Test**: Seed the reported graph and verify at use-case, persistence, and endpoint levels that the deployment sequence contains five stages: `E1/E2/E3`, `E`, `D`, `C`, `A/B`.

### Tests for User Story 2

- [X] T010 [P] [US2] Add five-stage reduced-graph assertions for the reported graph in `tests/test_micro_affinity_group_deployment_scope_use_case.py`
- [X] T011 [P] [US2] Add endpoint assertions for `deployment_sequence.bypassed_edges` and five ordered steps in `tests/test_micro_affinity_group_deployment_scope_endpoint.py`
- [X] T012 [P] [US2] Add persistence-backed assertions for reduced deployment-stage calculation in `tests/test_micro_affinity_group_deployment_scope_persistence.py`
- [X] T012a [P] [US2] Add stage-calculation assertions for the alternate cyclic regression to confirm that only active-path back-edges are excluded from reduced-graph layering in `tests/test_micro_affinity_group_deployment_scope_use_case.py`

### Implementation for User Story 2

- [X] T013 [US2] Update reduced-graph layering to exclude only path-scoped cyclic edges in `src/core/domain/micro_affinity_group_deployment_graph.py`
- [X] T014 [US2] Recompute `deployment_sequence.steps` from the corrected reduced graph in `src/core/use_cases/get_micro_affinity_group_deployment_scope.py`

**Checkpoint**: The reported cyclic graph now returns the expected bypassed edge list and five deployment stages.

---

## Phase 5: User Story 3 - Preserve Correct Behavior For Acyclic Graphs (Priority: P3)

**Goal**: Keep existing acyclic deployment-scope behavior unchanged while the cyclic fix lands.

**Independent Test**: Re-run existing acyclic deployment-scope scenarios and verify unchanged `graph_has_cycles`, empty bypassed edges, and stable deployment stage ordering.

### Tests for User Story 3

- [X] T015 [P] [US3] Strengthen acyclic non-regression assertions for cycle flags and stage ordering in `tests/test_micro_affinity_group_deployment_scope_use_case.py`
- [X] T016 [P] [US3] Strengthen acyclic API non-regression assertions in `tests/test_micro_affinity_group_deployment_scope_endpoint.py`
- [X] T017 [P] [US3] Strengthen acyclic persistence-backed non-regression assertions in `tests/test_micro_affinity_group_deployment_scope_persistence.py`

### Implementation for User Story 3

- [X] T018 [US3] Preserve deterministic ordering and empty-bypass behavior for acyclic graphs in `src/core/domain/micro_affinity_group_deployment_graph.py` and `src/core/use_cases/get_micro_affinity_group_deployment_scope.py`

**Checkpoint**: Existing acyclic deployment-scope responses remain unchanged after the cyclic fix.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the final change set against targeted, architectural, and full regression expectations.

- [X] T019 Run the targeted deployment-scope regression commands from `specs/014-fix-mag-cycle-detection/quickstart.md` against `tests/test_micro_affinity_group_deployment_scope_use_case.py`, `tests/test_micro_affinity_group_deployment_scope_endpoint.py`, and `tests/test_micro_affinity_group_deployment_scope_persistence.py`
- [X] T020 Run the architecture guard in `check_core_purity.py`
- [X] T021 Run the full regression command from `specs/014-fix-mag-cycle-detection/quickstart.md` against `tests/`
- [X] T021a Run and verify the existing deployment-scope `404` versus `422` non-regression scenarios in `tests/test_micro_affinity_group_deployment_scope_endpoint.py` and `tests/test_micro_affinity_group_deployment_scope_use_case.py`
- [X] T022 Update verified execution notes in `specs/014-fix-mag-cycle-detection/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies; start immediately.
- **Phase 2: Foundational**: Depends on Phase 1; blocks all user stories.
- **Phase 3: User Story 1**: Depends on Phase 2; establishes the corrected cyclic-edge selection rule.
- **Phase 4: User Story 2**: Depends on Phase 3; correct stage calculation requires the right bypassed edge set.
- **Phase 5: User Story 3**: Depends on Phases 3 and 4; acyclic regression validation is most reliable after the cyclic behavior is stable.
- **Phase 6: Polish**: Depends on all targeted user stories being complete.

### User Story Dependencies

- **US1 (P1)**: First deliverable and suggested MVP slice; it fixes the root defect in cyclic-edge identification.
- **US2 (P2)**: Depends on US1 because deployment-stage correctness requires the corrected cyclic-edge output.
- **US3 (P3)**: Depends on US1 and US2 because it verifies the final algorithm does not alter already-correct acyclic behavior.

### Within Each User Story

- Test tasks should be updated first and should fail against the unfixed implementation before runtime changes are completed.
- Pure-core graph helper changes should land before use-case orchestration changes.
- Each user story should be revalidated at its checkpoint before moving to the next dependent story.

### Parallel Opportunities

- `T003` and `T004` can run in parallel after the scope is confirmed in Phase 1.
- `T005`, `T006`, `T007`, `T007a`, and `T007b` can run in parallel because they touch separable US1 regression assertions and datasets.
- `T010`, `T011`, `T012`, and `T012a` can run in parallel because they cover different US2 stage-calculation assertions.
- `T015`, `T016`, and `T017` can run in parallel because they touch different US3 test files.
- `T019`, `T020`, and `T021a` can run in parallel once implementation is complete.

---

## Parallel Example: User Story 1

```bash
# Prepare all reported-graph regression tests together:
Task: "Add reported-graph back-edge regression coverage in tests/test_micro_affinity_group_deployment_scope_use_case.py"
Task: "Add reported-graph API regression asserting only E1 -> C is cyclic in tests/test_micro_affinity_group_deployment_scope_endpoint.py"
Task: "Add persistence-backed regression data and assertions for cyclic-edge selection in tests/test_micro_affinity_group_deployment_scope_persistence.py"
Task: "Add explicit assertions that immediate upstream consumer edges A -> C and B -> C remain present and non-cyclic in tests/test_micro_affinity_group_deployment_scope_use_case.py and tests/test_micro_affinity_group_deployment_scope_endpoint.py"
Task: "Add a second cyclic regression with an alternate branch or multi-path graph to verify that only edges pointing back to nodes on the current active traversal path are marked cyclic in tests/test_micro_affinity_group_deployment_scope_use_case.py"
```

---

## Parallel Example: User Story 2

```bash
# Prepare stage-calculation regressions together:
Task: "Add five-stage reduced-graph assertions for the reported graph in tests/test_micro_affinity_group_deployment_scope_use_case.py"
Task: "Add endpoint assertions for deployment_sequence.bypassed_edges and five ordered steps in tests/test_micro_affinity_group_deployment_scope_endpoint.py"
Task: "Add persistence-backed assertions for reduced deployment-stage calculation in tests/test_micro_affinity_group_deployment_scope_persistence.py"
Task: "Add stage-calculation assertions for the alternate cyclic regression to confirm that only active-path back-edges are excluded from reduced-graph layering in tests/test_micro_affinity_group_deployment_scope_use_case.py"
```

---

## Parallel Example: User Story 3

```bash
# Tighten acyclic regression coverage together before the final full-suite run:
Task: "Strengthen acyclic non-regression assertions for cycle flags and stage ordering in tests/test_micro_affinity_group_deployment_scope_use_case.py"
Task: "Strengthen acyclic API non-regression assertions in tests/test_micro_affinity_group_deployment_scope_endpoint.py"
Task: "Strengthen acyclic persistence-backed non-regression assertions in tests/test_micro_affinity_group_deployment_scope_persistence.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 to fix the reported cyclic-edge identification defect.
3. Validate the reported graph at use-case, persistence, and endpoint levels.
4. Stop and confirm the corrected cyclic-edge output before continuing into deployment-stage recalculation.

### Incremental Delivery

1. Deliver US1 to correct cyclic-edge selection.
2. Deliver US2 to correct deployment stages from the reduced graph.
3. Deliver US3 to prove acyclic behavior stays unchanged.
4. Finish with targeted validation, purity validation, and the full regression suite.

### Parallel Team Strategy

1. One developer handles the shared Phase 1 and Phase 2 graph-helper and use-case seams.
2. After Phase 2:
   - Developer A: US1 use-case and pure-core cycle detection
   - Developer B: US1 and US2 endpoint regression coverage
   - Developer C: US1 and US2 persistence-backed regression coverage
3. Rejoin for the acyclic non-regression pass and the final validation runs.

---

## Notes

- `[P]` tasks touch different files and have no dependency on unfinished work in the same phase.
- Every task includes exact repository paths so an implementation agent can execute without rediscovery.
- Suggested MVP scope is **User Story 1**, with **User Story 2** immediately after it because stage output remains operationally incorrect until the reduced-graph calculation is corrected.