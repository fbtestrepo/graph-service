# Tasks: Workload Test Scope Endpoint

**Input**: Design documents from /specs/016-workload-test-scope/
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/http-api.md, quickstart.md

**Tests**: Tests are required for this feature because the specification and user request explicitly require comprehensive happy-path, isolation, edge-case, validation, contract, and summary-math coverage.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish feature scaffolding used by all stories.

- [X] T001 Create workload test-scope use-case module scaffold in src/core/use_cases/get_workload_test_scope.py
- [X] T002 [P] Create endpoint test scaffold for POST /v1/micro-affinity-groups/workloads/test-scope in tests/test_workload_test_scope_endpoint.py
- [X] T003 [P] Create use-case test scaffold and sample builders in tests/test_workload_test_scope_use_case.py
- [X] T004 [P] Create persistence integration test scaffold with Mongo fixtures in tests/test_workload_test_scope_persistence.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared port, repository query capability, schema shell, and route wiring needed before user stories.

**CRITICAL**: No user story implementation starts before this phase is complete.

- [X] T005 Extend processed repository port with workload test-scope query contract in src/core/ports/micro_affinity_group_processed_repository.py
- [X] T006 Implement environment-scoped aggregation-first ownership resolution for workload test scope in src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py
- [X] T007 [P] Define request and response Pydantic model shell in src/adapters/inbound/api/schemas/workload_test_scope.py
- [X] T008 [P] Add timestamp and summary helper shell in src/core/use_cases/get_workload_test_scope.py
- [X] T009 Wire POST /workloads/test-scope route skeleton and dependencies in src/adapters/inbound/api/routers/micro_affinity_groups.py

**Checkpoint**: Foundation complete; user story development can begin.

---

## Phase 3: User Story 1 - Build Test Scope For Changed Workloads (Priority: P1)

**Goal**: Resolve affected workload relationships for changed workloads from source and destination directions.

**Independent Test**: Send valid POST requests with known workloads and verify resolved changed_workloads plus unique affected_workload_relationships for source, destination, and dual-role cases in the requested environment.

### Tests for User Story 1

- [X] T010 [P] [US1] Add use-case test for source-side relationship traversal in tests/test_workload_test_scope_use_case.py
- [X] T011 [P] [US1] Add use-case test for destination-side relationship traversal in tests/test_workload_test_scope_use_case.py
- [X] T012 [P] [US1] Add use-case test for dual-role changed workload coverage without duplicates in tests/test_workload_test_scope_use_case.py
- [X] T013 [P] [US1] Add endpoint integration tests for source, destination, and dual-role success paths in tests/test_workload_test_scope_endpoint.py
- [X] T014 [P] [US1] Add persistence integration test for environment isolation across production and staging in tests/test_workload_test_scope_persistence.py

### Implementation for User Story 1

- [X] T015 [US1] Implement source-side and destination-side candidate resolution flow in src/core/use_cases/get_workload_test_scope.py
- [X] T016 [US1] Implement workload-to-micro-AG ownership mapping from repository results in src/core/use_cases/get_workload_test_scope.py
- [X] T017 [US1] Implement affected_workload_relationships deduplication and ordering in src/core/use_cases/get_workload_test_scope.py
- [X] T018 [US1] Connect POST endpoint execution to workload test-scope use case in src/adapters/inbound/api/routers/micro_affinity_groups.py

**Checkpoint**: US1 independently returns complete affected relationship scope for known workloads.

---

## Phase 4: User Story 2 - Detect Unknown Workloads (Priority: P2)

**Goal**: Report unknown workloads from unmatched input IDs and unresolved relationship endpoints while preserving no-data and empty-input behavior.

**Independent Test**: Send mixed known and unknown inputs, unresolved endpoint scenarios, empty lists, and no-data environments; verify unknown_workloads content and summary consistency.

### Tests for User Story 2

- [X] T019 [P] [US2] Add use-case test for unknown input workload detection in tests/test_workload_test_scope_use_case.py
- [X] T020 [P] [US2] Add use-case test for unresolved relationship endpoint exclusion and unknown reporting in tests/test_workload_test_scope_use_case.py
- [X] T020a [P] [US2] Add use-case test for ambiguous workload ownership in one environment returning 422 in tests/test_workload_test_scope_use_case.py
- [X] T021 [P] [US2] Add endpoint test for empty changed_workloads returning 200 with zero summary in tests/test_workload_test_scope_endpoint.py
- [X] T022 [P] [US2] Add endpoint test for no-records environment returning 200 with unknowns from deduplicated input in tests/test_workload_test_scope_endpoint.py
- [X] T023 [P] [US2] Add persistence integration test for unresolved endpoint handling in tests/test_workload_test_scope_persistence.py

### Implementation for User Story 2

- [X] T024 [US2] Implement first-seen deduplication of input workload_asset_id values in src/core/use_cases/get_workload_test_scope.py
- [X] T025 [US2] Implement changed_workloads and unknown_workloads partitioning in src/core/use_cases/get_workload_test_scope.py
- [X] T026 [US2] Implement unresolved relationship exclusion and unknown accumulation in src/core/use_cases/get_workload_test_scope.py
- [X] T026a [US2] Implement ambiguous ownership detection by raising a domain exception in src/core/use_cases/get_workload_test_scope.py with exception type in src/core/exceptions/ambiguous_workload_ownership.py; map this exception to 422 in infrastructure error handlers.
- [X] T027 [US2] Implement environment no-data fallback payload behavior in src/core/use_cases/get_workload_test_scope.py

**Checkpoint**: US2 independently handles unknown, unresolved, empty-input, and no-data scenarios.

---

## Phase 5: User Story 3 - Preserve Contract Shape And Casing (Priority: P3)

**Goal**: Enforce snake_case response shape, deterministic ordering, summary math correctness, and validation behavior.

**Independent Test**: Validate response payload structure and casing against sample contract, verify summary math on overlapping relationships, and assert 422 for missing or blank environment.

### Tests for User Story 3

- [X] T028 [P] [US3] Add endpoint contract test asserting full nested response parity with sample output shape and snake_case keys in tests/test_workload_test_scope_endpoint.py
- [X] T029 [P] [US3] Add use-case summary-math tests for distinct affected workloads and micro AGs in tests/test_workload_test_scope_use_case.py
- [X] T030 [P] [US3] Add endpoint validation tests for missing and blank environment returning 422 with explicit no-processing assertions in tests/test_workload_test_scope_endpoint.py
- [X] T030a [P] [US3] Add endpoint malformed JSON test returning 400 problem-details in tests/test_workload_test_scope_endpoint.py
- [X] T031 [P] [US3] Add persistence determinism test for sorted affected_workload_relationships in tests/test_workload_test_scope_persistence.py

### Implementation for User Story 3

- [X] T032 [US3] Finalize request and response nested Pydantic models in src/adapters/inbound/api/schemas/workload_test_scope.py
- [X] T033 [US3] Attach request and response models to POST route in src/adapters/inbound/api/routers/micro_affinity_groups.py
- [X] T034 [US3] Implement summary counter derivation and UTC timestamp formatting in src/core/use_cases/get_workload_test_scope.py
- [X] T035 [US3] Ensure validation and problem-details behavior for query and body errors in src/infrastructure/errors/validation.py and tests/test_workload_test_scope_endpoint.py

**Checkpoint**: US3 independently guarantees contract integrity, deterministic ordering, and validation semantics.

---

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Run full verification and capture execution evidence.

- [X] T036 [P] Update quickstart verification notes with executed command outcomes in specs/016-workload-test-scope/quickstart.md
- [X] T037 Run targeted workload test-scope suites in tests/test_workload_test_scope_use_case.py, tests/test_workload_test_scope_endpoint.py, and tests/test_workload_test_scope_persistence.py
- [X] T038 Run micro-affinity-group regression suites in tests/test_micro_affinity_groups_endpoint.py, tests/test_micro_affinity_groups_persistence.py, and tests/test_micro_affinity_group_use_case.py
- [X] T039 Run architecture purity guard in check_core_purity.py
- [X] T040 Run full regression suite in tests/
- [X] T041 [P] Run workload test-scope latency smoke validation and assert p95 <= 300 ms and p99 <= 600 ms in tests/test_perf_smoke_workload_test_scope.py

---

## Dependencies and Execution Order

### Phase Dependencies

- Setup (Phase 1): no dependencies.
- Foundational (Phase 2): depends on Setup completion and blocks all user stories.
- User Stories (Phases 3 to 5): depend on Foundational completion.
- Polish (Phase 6): depends on completion of all user stories.

### User Story Dependencies

- User Story 1 (P1): can start immediately after Foundational completion.
- User Story 2 (P2): can start after Foundational completion; usually follows US1 for incremental delivery.
- User Story 3 (P3): can start after Foundational completion; usually follows US1 and US2 for incremental delivery.

### Within Each User Story

- Write tests before implementation and verify they fail first.
- Implement core use-case behavior before final router and schema wiring checks.
- Confirm each story checkpoint before proceeding.

### Parallel Opportunities

- Setup: T002, T003, and T004 can run in parallel.
- Foundational: T007 and T008 can run in parallel after T005 and T006 sequencing is clear.
- US1: T010 to T014 can run in parallel.
- US2: T019 to T023 can run in parallel.
- US3: T028 to T031 plus T030a can run in parallel.
- Polish: T036 can run in parallel with test execution tasks.

---

## Parallel Example: User Story 1

```bash
Task: "Add use-case test for source-side relationship traversal in tests/test_workload_test_scope_use_case.py"
Task: "Add use-case test for destination-side relationship traversal in tests/test_workload_test_scope_use_case.py"
Task: "Add use-case test for dual-role changed workload coverage without duplicates in tests/test_workload_test_scope_use_case.py"
Task: "Add endpoint integration tests for source, destination, and dual-role success paths in tests/test_workload_test_scope_endpoint.py"
Task: "Add persistence integration test for environment isolation across production and staging in tests/test_workload_test_scope_persistence.py"
```

---

## Parallel Example: User Story 2

```bash
Task: "Add use-case test for unknown input workload detection in tests/test_workload_test_scope_use_case.py"
Task: "Add use-case test for unresolved relationship endpoint exclusion and unknown reporting in tests/test_workload_test_scope_use_case.py"
Task: "Add use-case test for ambiguous workload ownership in one environment returning 422 in tests/test_workload_test_scope_use_case.py"
Task: "Add endpoint test for empty changed_workloads returning 200 with zero summary in tests/test_workload_test_scope_endpoint.py"
Task: "Add endpoint test for no-records environment returning 200 with unknowns from deduplicated input in tests/test_workload_test_scope_endpoint.py"
Task: "Add persistence integration test for unresolved endpoint handling in tests/test_workload_test_scope_persistence.py"
```

---

## Parallel Example: User Story 3

```bash
Task: "Add endpoint contract test asserting full nested response parity with sample output shape and snake_case keys in tests/test_workload_test_scope_endpoint.py"
Task: "Add use-case summary-math tests for distinct affected workloads and micro AGs in tests/test_workload_test_scope_use_case.py"
Task: "Add endpoint validation tests for missing and blank environment returning 422 with explicit no-processing assertions in tests/test_workload_test_scope_endpoint.py"
Task: "Add endpoint malformed JSON test returning 400 problem-details in tests/test_workload_test_scope_endpoint.py"
Task: "Add persistence determinism test for sorted affected_workload_relationships in tests/test_workload_test_scope_persistence.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3.
3. Validate User Story 1 independently.
4. Demo or deploy MVP behavior.

### Incremental Delivery

1. Deliver US1 relationship resolution MVP.
2. Deliver US2 unknown and unresolved handling.
3. Deliver US3 contract and validation guarantees.
4. Execute Phase 6 verification.

### Parallel Team Strategy

1. Developer A: core use-case logic in src/core/use_cases/get_workload_test_scope.py.
2. Developer B: repository query and router integration in src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py and src/adapters/inbound/api/routers/micro_affinity_groups.py.
3. Developer C: endpoint, use-case, and persistence test suites in tests/test_workload_test_scope_*.py.

---

## Notes

- [P] marks tasks that can be performed in parallel because they touch independent files.
- [US1], [US2], and [US3] labels map tasks directly to prioritized user stories.
- Suggested MVP scope is Phase 3 (User Story 1).
- Keep core logic framework-agnostic and keep Mongo and HTTP concerns in adapters.
