# Tasks: MAG Upsert Uniqueness

**Input**: Design documents from `/specs/012-mag-upsert-uniqueness/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/http-api.md, quickstart.md

**Tests**: Tests are required for this feature because the specification and planning artifacts
explicitly call for pytest synchronization, duplicate-conflict coverage, overwrite coverage across
architecture versions, and required non-perf regression validation.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated
independently.

## Phase 1: Setup (Shared Contract Alignment)

**Purpose**: Align shared MAG contract wording and codegen inputs before runtime changes.

- [X] T001 Review and, if needed, update identity wording in `specs/001-service-skeleton/contracts/micro_affinity_group.schema.json` so it describes `micro_ag_id + environment` as the write identity without changing payload fields

- [X] T002 [P] Review and, if needed, update identity wording in `specs/001-service-skeleton/contracts/micro_affinity_group_processed.schema.json` and `src/adapters/inbound/api/schemas/README.md` to reflect pair-based MAG identity and unchanged architecture_version validation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the shared domain and port changes required before any story-specific implementation.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T003 Add `DuplicateMicroAffinityGroupIdentity` in `src/core/exceptions/duplicate_micro_affinity_group_identity.py` for pre-existing duplicate raw or processed identity pairs
- [X] T004 [P] Map `DuplicateMicroAffinityGroupIdentity` to `409 Conflict` in `src/infrastructure/errors/mappers.py` and register it in `src/infrastructure/errors/handlers.py`
- [X] T005 Update MAG repository ABCs in `src/core/ports/micro_affinity_group_repository.py` and `src/core/ports/micro_affinity_group_processed_repository.py` to use pair-based upsert semantics and expose identity-count queries

**Checkpoint**: Shared domain error handling and repository contracts are ready for story work.

---

## Phase 3: User Story 1 - Overwrite By MAG And Environment (Priority: P1) 🎯 MVP

**Goal**: Make raw and processed MAG writes key off `micro_ag_id + environment`, overwrite cleanly when `architecture_version` changes, and reject corrupted duplicate state.

**Independent Test**: Submit two valid payloads with the same `micro_ag_id` and `environment` but different `architecture_version` values and confirm one raw record and one processed record remain; seed duplicate records for one identity pair and confirm the endpoint returns `409 Conflict` without modifying either collection.

### Tests for User Story 1

- [X] T006 [P] [US1] Update pair-based fake repositories and overwrite assertions in `tests/test_micro_affinity_group_use_case.py`
- [X] T007 [US1] Update overwrite, duplicate-conflict, rollback, and status-code coverage in `tests/test_micro_affinity_groups_endpoint.py`
- [X] T008 [US1] Update pair-based overwrite, duplicate-conflict, partial-state repair, and processed-write-failure rollback persistence coverage in `tests/test_micro_affinity_groups_persistence.py`

### Implementation for User Story 1

- [X] T009 [US1] Implement pair-based duplicate detection, partial-state repair, created-flag derivation, and overwrite flow in `src/core/use_cases/upsert_micro_affinity_group.py`
- [X] T010 [P] [US1] Implement pair-based count and full-replace upsert behavior in `src/adapters/outbound/mongodb/micro_affinity_group_repository.py`
- [X] T011 [P] [US1] Implement pair-based count and full-replace upsert behavior in `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py`

**Checkpoint**: Same-pair requests overwrite rather than fork by `architecture_version`, and corrupted duplicate state fails with `409 Conflict`.

---

## Phase 4: User Story 2 - Preserve Payload Validation And Response Shape (Priority: P2)

**Goal**: Keep `architecture_version` required and validated as before while ensuring responses and persisted documents still carry the submitted value.

**Independent Test**: Send valid and invalid MAG payloads and confirm that `architecture_version` validation behavior is unchanged while successful responses still echo the submitted `architecture_version`.

### Tests for User Story 2

- [X] T012 [US2] Expand validation and response-shape assertions in `tests/test_micro_affinity_groups_endpoint.py` to prove missing or invalid `micro_ag_id`, missing or invalid `environment`, and invalid `architecture_version` still fail with existing validation behavior while successful responses still echo the submitted `architecture_version`

### Implementation for User Story 2

- [X] T013 [US2] Regenerate `src/adapters/inbound/api/schemas/micro_affinity_group.py` and `src/adapters/inbound/api/schemas/micro_affinity_group_processed.py` with `generate_inbound_models.sh` if the updated contract wording changes generated schema output
- [X] T014 [US2] Update router wiring for any repository signature changes in `src/adapters/inbound/api/routers/micro_affinity_groups.py` while preserving snake_case request/response handling and `201`/`200` semantics

**Checkpoint**: Validation rules and response shape remain stable even though persistence identity changed.

---

## Phase 5: User Story 3 - Keep Environment Isolation (Priority: P3)

**Goal**: Preserve separate MAG records across different environments even after narrowing the write identity.

**Independent Test**: Submit valid payloads with the same `micro_ag_id` to two environments and confirm each environment keeps its own raw and processed record pair with `201 Created` for the new environment.

### Tests for User Story 3

- [X] T015 [US3] Update coexistence-across-environments assertions in `tests/test_micro_affinity_groups_endpoint.py` and `tests/test_micro_affinity_groups_persistence.py` to prove environment remains part of the identity boundary
- [X] T016 [P] [US3] Update pair-based fake repository keys in `tests/test_perf_smoke_micro_affinity_groups.py` to preserve environment isolation in perf-smoke coverage

### Implementation for User Story 3

- [X] T017 [US3] Verify pair-based repository and use-case logic preserve separate records for different environments in `src/core/use_cases/upsert_micro_affinity_group.py`, `src/adapters/outbound/mongodb/micro_affinity_group_repository.py`, and `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py`

**Checkpoint**: Different environments still coexist cleanly under the narrowed identity rule.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, cleanup, and feature-document synchronization.

- [X] T018 Run the focused MAG regression suites from `specs/012-mag-upsert-uniqueness/quickstart.md`
- [X] T019 Run the architecture guard `check_core_purity.py` from `check_core_purity.py`
- [X] T020 Run the required non-perf regression suite documented in `specs/012-mag-upsert-uniqueness/quickstart.md`
- [X] T021 Update verified implementation notes and commands in `specs/012-mag-upsert-uniqueness/quickstart.md` and `specs/012-mag-upsert-uniqueness/contracts/http-api.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup**: No dependencies; start immediately.
- **Phase 2: Foundational**: Depends on Phase 1; blocks all user stories.
- **Phase 3: User Story 1**: Depends on Phase 2; delivers the MVP.
- **Phase 4: User Story 2**: Depends on Phase 2; can proceed after or alongside US1, but shares endpoint/schema files.
- **Phase 5: User Story 3**: Depends on Phase 2; can proceed after or alongside US1, but shares endpoint/persistence test files.
- **Phase 6: Polish**: Depends on all targeted user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories; this is the minimum releasable slice.
- **US2 (P2)**: Depends on the foundational contract/port alignment but not on US1 business logic beyond shared files.
- **US3 (P3)**: Depends on the foundational identity rewrite and uses the same repository behavior introduced for US1.

### Within Each User Story

- Test tasks should be updated first and fail against the old behavior before implementation changes are completed.
- Core orchestration changes precede adapter rewrites when a story depends on new port behavior.
- Persistence and endpoint assertions should be re-run after each story checkpoint.

### Parallel Opportunities

- `T002` can run in parallel with `T001`.
- `T004` can run in parallel with `T003` once the new exception name is agreed.
- `T010` and `T011` can run in parallel after `T005` and alongside `T009` once the port contract is settled.
- `T006` can run in parallel with `T007` or `T008` because they touch different test files.
- `T016` can run in parallel with `T015` because it touches the perf-smoke test file only.

---

## Parallel Example: User Story 1

```bash
# Launch the first wave of US1 test synchronization together:

Task: "Update pair-based fake repositories and overwrite assertions in tests/test_micro_affinity_group_use_case.py"
Task: "Update overwrite, duplicate-conflict, rollback, and status-code coverage in tests/test_micro_affinity_groups_endpoint.py"
Task: "Update pair-based overwrite, duplicate-conflict, partial-state repair, and processed-write-failure rollback persistence coverage in tests/test_micro_affinity_groups_persistence.py"

# Launch the repository adapter changes together after the port contract is updated:
Task: "Implement pair-based count and full-replace upsert behavior in src/adapters/outbound/mongodb/micro_affinity_group_repository.py"
Task: "Implement pair-based count and full-replace upsert behavior in src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py"
```

---

## Parallel Example: User Story 3

```bash
# Environment-isolation test updates can be split across distinct files:
Task: "Update coexistence-across-environments assertions in tests/test_micro_affinity_groups_endpoint.py and tests/test_micro_affinity_groups_persistence.py"
Task: "Update pair-based fake repository keys in tests/test_perf_smoke_micro_affinity_groups.py to preserve environment isolation in perf-smoke coverage"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 for pair-based overwrite and duplicate-conflict behavior.
3. Validate the focused MAG tests for overwrite and conflict handling.
4. Stop and review before broadening into validation-shape and perf coverage.

### Incremental Delivery

1. Deliver US1 to establish the new write identity and conflict handling.
2. Deliver US2 to prove the payload contract and response shape remain stable.
3. Deliver US3 to confirm environment isolation still holds.
4. Finish with required non-perf regression and doc verification in Phase 6.

### Parallel Team Strategy

1. One developer handles contract/port/exception groundwork in Phases 1 and 2.
2. After Phase 2:
   - Developer A: US1 core + repository identity rewrite
   - Developer B: US2 schema/endpoint validation alignment
   - Developer C: US3 environment-isolation test updates and perf-smoke sync
3. Rejoin for the required non-perf regression pass and feature-doc verification.

---

## Notes

- `[P]` tasks touch different files and have no dependency on unfinished work in the same phase.
- Every task includes exact file paths so an implementation agent can execute without re-discovery.
- MongoDB index management remains out of scope for every task in this file.