# Tasks: MAG Deployment Scope

**Input**: Design documents from `/specs/013-mag-deployment-scope/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are required for this feature because the specification and planning artifacts explicitly call for unit, endpoint, persistence-backed, architecture-purity, and full regression coverage, including 30-hop truncation, cycle handling, and `404` versus `422` behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Phase 1: Setup (Contract And Codegen Alignment)

**Purpose**: Align the new deployment-scope contract artifacts and response-model generation path before runtime changes.

- [X] T001 Review and, if needed, finalize deployment-scope response contract semantics in `specs/013-mag-deployment-scope/contracts/http-api.md` and `specs/013-mag-deployment-scope/contracts/openapi.yaml`
- [X] T002 [P] Stage deployment-scope schema generation inputs in `generate_inbound_models.sh` and `src/adapters/inbound/api/schemas/README.md`
- [X] T003 [P] Verify the sample response remains the runtime source of truth in `specs/samples/micro-affinity-group/deployment-scope.json` and `specs/013-mag-deployment-scope/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the shared domain, port, and wiring changes required before any user story can be completed.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T004 Add deployment-scope domain exceptions in `src/core/exceptions/micro_affinity_group_not_found.py` and `src/core/exceptions/micro_affinity_group_graph_resolution_error.py`
- [X] T005 [P] Extend processed MAG read capabilities in `src/core/ports/micro_affinity_group_processed_repository.py` for root lookup, environment-scoped asset ownership matching, and frontier expansion reads
- [X] T006 [P] Create an initial hand-maintained deployment-scope response-model scaffold in `src/adapters/inbound/api/schemas/micro_affinity_group_deployment_scope.py` so endpoint and use-case work can proceed before final code generation is wired
- [X] T007 [P] Register deployment-scope dependencies and repository access in `src/adapters/inbound/api/dependencies/wiring.py` and `src/infrastructure/main.py`
- [X] T008 Add new deployment-scope exception classes to the global problem-details mapping table in `src/infrastructure/errors/mappers.py` and register their handlers in `src/infrastructure/errors/handlers.py`

**Checkpoint**: Shared exception, port, schema, and wiring surfaces are ready for endpoint work.

---

## Phase 3: User Story 1 - Retrieve Deployment Scope (Priority: P1) 🎯 MVP

**Goal**: Return a snake_case deployment-scope document for a resolvable MAG/environment pair, including the root MAG, one inverse upstream hop, and downstream traversal within the feature’s 30-hop contract boundary.

**Independent Test**: Seed one environment with processed MAG documents for a linear or branching graph that resolves within the 30-hop traversal boundary, call `GET /v1/micro-affinity-groups/{id}/deployment-scope?environment=...`, and verify the response shape, resolved edges, empty-graph handling, and snake_case payload fields.

### Tests for User Story 1

- [X] T009 [P] [US1] Add successful traversal and empty-graph coverage in `tests/test_micro_affinity_group_deployment_scope_use_case.py`
- [X] T010 [P] [US1] Add environment-scoped asset-join, deduplicated edge, and read-only no-write coverage in `tests/test_micro_affinity_group_deployment_scope_persistence.py`
- [X] T011 [P] [US1] Add successful endpoint coverage for snake_case deployment-scope responses, sample-contract conformance, and Zulu `effective_date` formatting in `tests/test_micro_affinity_group_deployment_scope_endpoint.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement environment-scoped root lookup and workload-ownership traversal queries in `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py`
- [X] T013 [US1] Implement deployment-scope graph assembly and empty-graph response generation in `src/core/use_cases/get_micro_affinity_group_deployment_scope.py`
- [X] T014 [P] [US1] Replace the initial scaffold with the generated and finalized deployment-scope response schema in `src/adapters/inbound/api/schemas/micro_affinity_group_deployment_scope.py` via `generate_inbound_models.sh` and confirm it matches the feature contract
- [X] T015 [US1] Add `GET /v1/micro-affinity-groups/{id}/deployment-scope` to `src/adapters/inbound/api/routers/micro_affinity_groups.py`

**Checkpoint**: The endpoint returns correct deployment scope for resolvable graphs and for a root MAG with no edges.

---

## Phase 4: User Story 2 - Classify Missing Root And Broken Graphs Correctly (Priority: P2)

**Goal**: Distinguish a missing root MAG from downstream graph-resolution failures so the endpoint returns `404` only for missing `(micro_ag_id, environment)` roots and `422` for broken downstream joins after root discovery.

**Independent Test**: Request the endpoint once for a missing root pair and once for an existing root whose downstream workload ownership is missing, malformed, or ambiguous, then confirm the route returns `404` in the first case and `422` in the second.

### Tests for User Story 2

- [X] T016 [P] [US2] Add missing-root and downstream-failure use-case coverage in `tests/test_micro_affinity_group_deployment_scope_use_case.py`
- [X] T017 [P] [US2] Add ambiguous-join and malformed-source persistence coverage in `tests/test_micro_affinity_group_deployment_scope_persistence.py`
- [X] T018 [P] [US2] Add `404` versus `422` endpoint coverage in `tests/test_micro_affinity_group_deployment_scope_endpoint.py`

### Implementation for User Story 2

- [X] T019 [US2] Implement missing-root and downstream-resolution failure handling in `src/core/use_cases/get_micro_affinity_group_deployment_scope.py`
- [X] T020 [US2] Surface missing and ambiguous ownership matches as deployment-scope failures in `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py`
- [X] T021 [US2] Wire the deployment-scope route to raise the mapped domain exceptions and verify the router returns the expected problem-details responses without route-local HTTP classification logic in `src/adapters/inbound/api/routers/micro_affinity_groups.py`, `src/infrastructure/errors/mappers.py`, and `src/infrastructure/errors/handlers.py`

**Checkpoint**: The new route preserves the constitution rule that only a missing root returns `404`.

---

## Phase 5: User Story 3 - Surface Cycles In Deployment Planning (Priority: P3)

**Goal**: Surface cycles explicitly in the response and compute a deterministic, dependency-first deployment sequence with lexicographic ordering and 30-hop bounded traversal.

**Independent Test**: Seed a cyclic processed-MAG graph plus a long downstream chain, call the endpoint, and verify cyclic edge marking, `bypassed_edges`, grouped deployment layers, lexicographic ordering, and graceful truncation at 30 hops.

### Tests for User Story 3

- [X] T022 [P] [US3] Add cycle reduction, parallel-layer, ordering, and 30-hop boundary coverage in `tests/test_micro_affinity_group_deployment_scope_use_case.py`
- [X] T023 [P] [US3] Add cyclic graph and deployment-sequence persistence coverage in `tests/test_micro_affinity_group_deployment_scope_persistence.py`
- [X] T024 [P] [US3] Add cyclic endpoint response coverage in `tests/test_micro_affinity_group_deployment_scope_endpoint.py`

### Implementation for User Story 3

- [X] T025 [P] [US3] Add deterministic MAG graph reduction helpers in `src/core/domain/micro_affinity_group_deployment_graph.py`
- [X] T026 [US3] Implement cycle detection, bypassed-edge marking, lexicographic ordering, deployment layering, and 30-hop truncation in `src/core/use_cases/get_micro_affinity_group_deployment_scope.py`
- [X] T027 [US3] Return ordered cyclic edge metadata and deployment steps in `src/adapters/inbound/api/schemas/micro_affinity_group_deployment_scope.py` and `src/adapters/inbound/api/routers/micro_affinity_groups.py`

**Checkpoint**: Cyclic graphs produce deterministic `dependency_graph` and `deployment_sequence` outputs that remain stable across repeated requests.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish validation, protect architecture boundaries, and sync verification docs.

- [X] T028 Run the focused deployment-scope suites from `specs/013-mag-deployment-scope/quickstart.md`
- [X] T029 Run the architecture guard in `check_core_purity.py`
- [X] T030 Run the full regression suite documented in `specs/013-mag-deployment-scope/quickstart.md`
- [X] T031 Update verified implementation notes and commands in `specs/013-mag-deployment-scope/quickstart.md` and `specs/013-mag-deployment-scope/contracts/http-api.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies; start immediately.
- **Phase 2: Foundational**: Depends on Phase 1; blocks all user stories.
- **Phase 3: User Story 1**: Depends on Phase 2; delivers the successful-response path and initial deployment-scope endpoint surface.
- **Phase 4: User Story 2**: Depends on Phase 2 and the shared route/use-case surface introduced for US1.
- **Phase 5: User Story 3**: Depends on Phase 2 and the shared route/use-case surface introduced for US1.
- **Phase 6: Polish**: Depends on all targeted user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Delivers the successful-response path for the deployment-scope endpoint.
- **US2 (P2)**: Required with US1 for the minimum releasable slice because constitution-mandated `404` versus `422` graph-error behavior is part of the baseline endpoint contract.
- **US3 (P3)**: Builds on the deployment-scope route and use case from US1 to add deterministic cycle handling, layered deployment sequencing, and the bounded long-chain traversal behavior.

### Within Each User Story

- Test tasks should be created or updated first and fail against the incomplete implementation before runtime changes are finished.
- Repository and pure-core graph logic should land before router-only adjustments.
- Response model generation should be synchronized before endpoint assertions are finalized.
- Each story should be revalidated at its checkpoint before starting the next dependent story.

### Parallel Opportunities

- `T002` and `T003` can run in parallel after `T001` confirms the contract surface.
- `T005`, `T006`, and `T007` can run in parallel after `T004` defines the exception names and failure model.
- `T009`, `T010`, and `T011` can run in parallel because they touch different US1 test files.
- `T014` can run in parallel with `T012` and `T013` once the contract/codegen staging path is settled.
- `T016`, `T017`, and `T018` can run in parallel because they cover different US2 test surfaces.
- `T022`, `T023`, and `T024` can run in parallel because they cover different US3 test surfaces.
- `T025` can run in parallel with `T023` and `T024` while the use-case integration in `T026` is still pending.

---

## Parallel Example: User Story 1

```bash
# Launch the first wave of US1 tests together:
Task: "Add successful traversal and empty-graph coverage in tests/test_micro_affinity_group_deployment_scope_use_case.py"
Task: "Add environment-scoped asset-join, deduplicated edge, and read-only no-write coverage in tests/test_micro_affinity_group_deployment_scope_persistence.py"
Task: "Add successful endpoint coverage for snake_case deployment-scope responses, sample-contract conformance, and Zulu effective_date formatting in tests/test_micro_affinity_group_deployment_scope_endpoint.py"

# After the repository contract is stable, split implementation across adapter and schema work:
Task: "Implement environment-scoped root lookup and workload-ownership traversal queries in src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py"
Task: "Replace the initial scaffold with the generated and finalized deployment-scope response schema in src/adapters/inbound/api/schemas/micro_affinity_group_deployment_scope.py via generate_inbound_models.sh and confirm it matches the feature contract"
```

---

## Parallel Example: User Story 2

```bash
# Error-path tests can be prepared together:
Task: "Add missing-root and downstream-failure use-case coverage in tests/test_micro_affinity_group_deployment_scope_use_case.py"
Task: "Add ambiguous-join and malformed-source persistence coverage in tests/test_micro_affinity_group_deployment_scope_persistence.py"
Task: "Add 404 versus 422 endpoint coverage in tests/test_micro_affinity_group_deployment_scope_endpoint.py"
```

---

## Parallel Example: User Story 3

```bash
# Cycle-oriented tests can be prepared in parallel while the pure-core helper is built:
Task: "Add cycle reduction, parallel-layer, ordering, and 30-hop boundary coverage in tests/test_micro_affinity_group_deployment_scope_use_case.py"
Task: "Add cyclic graph and deployment-sequence persistence coverage in tests/test_micro_affinity_group_deployment_scope_persistence.py"
Task: "Add cyclic endpoint response coverage in tests/test_micro_affinity_group_deployment_scope_endpoint.py"
Task: "Add deterministic MAG graph reduction helpers in src/core/domain/micro_affinity_group_deployment_graph.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 And 2)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 to deliver the successful read-only deployment-scope flow for resolvable graphs.
3. Complete Phase 4 to enforce constitution-compliant `404` versus `422` behavior for graph-resolution failures.
4. Validate the focused US1 and US2 tests for successful traversal, empty-graph handling, missing-root handling, and downstream-failure classification.
5. Stop and review the contract and response shape before broadening into cycle behavior and long-chain traversal.

### Incremental Delivery

1. Deliver US1 to establish the endpoint, repository reads, and response model.
2. Deliver US2 to lock in constitution-compliant `404` versus `422` behavior.
3. Deliver US3 to add deterministic cycle handling, deployment sequencing, and 30-hop truncation.
4. Finish with purity and full regression validation in Phase 6.

### Parallel Team Strategy

1. One developer handles Phase 1 and the shared Phase 2 groundwork.
2. After Phase 2:
   - Developer A: US1 repository and use-case traversal flow
   - Developer B: US1 schema and router integration, then US2 endpoint/problem-details coverage
   - Developer C: US3 pure-core cycle helpers and long-graph test preparation
3. Rejoin for the focused deployment-scope verification, purity guard, and full regression pass.

---

## Notes

- `[P]` tasks touch different files and have no dependency on unfinished work in the same phase.
- Every task includes exact file paths so an implementation agent can execute without rediscovery.
- The suggested MVP scope is **User Stories 1 and 2 together** because constitution-required `404` versus `422` behavior is part of the baseline contract for this graph-traversal endpoint.