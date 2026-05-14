---

description: "Task list for implementing 008-add-mag-relationships"

---

# Tasks: Micro Affinity Group Relationship Enrichment

**Input**: Design documents from `specs/008-add-mag-relationships/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Authoritative service contracts/codegen inputs**: `specs/001-service-skeleton/contracts/` and `generate_inbound_models.sh`

## Phase 1: Setup (Contracts + Codegen)

**Purpose**: Add the processed response contract to the authoritative service-contract path and generate the new inbound response model before implementation begins.

- [x] T001 Add authoritative processed response schema `specs/001-service-skeleton/contracts/micro_affinity_group_processed.schema.json` from `specs/008-add-mag-relationships/contracts/micro_affinity_group_processed.schema.json`
- [x] T002 Update `specs/001-service-skeleton/contracts/openapi.yaml` so `POST /micro-affinity-groups` returns `micro_affinity_group_processed.schema.json` for `201` and `200` responses
- [x] T003 [P] Update `specs/001-service-skeleton/contracts/http-api.md` to document transactional raw-plus-processed writes and the enriched response body for `POST /micro-affinity-groups`
- [x] T004 [P] Sync `specs/008-add-mag-relationships/contracts/http-api.md`, `specs/008-add-mag-relationships/contracts/openapi.yaml`, and `specs/008-add-mag-relationships/contracts/micro_affinity_group_processed.schema.json` with the finalized authoritative service contracts
- [x] T005 Update `generate_inbound_models.sh` to generate `src/adapters/inbound/api/schemas/micro_affinity_group_processed.py` from `specs/001-service-skeleton/contracts/micro_affinity_group_processed.schema.json`
- [x] T006 Run `./generate_inbound_models.sh` and update `src/adapters/inbound/api/schemas/README.md` to map `specs/001-service-skeleton/contracts/micro_affinity_group_processed.schema.json` to `src/adapters/inbound/api/schemas/micro_affinity_group_processed.py`

---

## Phase 2: Foundational (Ports, Transactions, Wiring)

**Purpose**: Add the new ports, transaction boundary, session-aware adapters, and test fixture support required before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Add processed-document repository port `src/core/ports/micro_affinity_group_processed_repository.py` for upserting transformed records in `micro-affinity-groups-processed`
- [x] T008 Add transaction boundary port `src/core/ports/transaction_manager.py` for executing the raw-write plus processed-write unit of work inside one transaction
- [x] T009 Extend `src/core/ports/micro_affinity_group_repository.py` and `src/core/ports/application_architecture_repository.py` with optional session-aware method signatures needed by transactional use-case orchestration
- [x] T010 [P] Implement `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py` for full-replacement upserts into `micro-affinity-groups-processed`
- [x] T011 [P] Implement `src/adapters/outbound/mongodb/transaction_manager.py` using MongoDB client sessions and `with_transaction(...)`
- [x] T012 Update `src/adapters/outbound/mongodb/micro_affinity_group_repository.py` and `src/adapters/outbound/mongodb/application_architecture_repository.py` so their reads and writes participate in an injected MongoDB session
- [x] T013 Update `src/adapters/inbound/api/dependencies/wiring.py` and `src/infrastructure/main.py` to register and expose `micro_affinity_group_processed_repository` and `transaction_manager`
- [x] T014 Update `tests/conftest.py` to provide a replica-set-capable MongoDB fixture for transactional integration tests

**Checkpoint**: Transaction-aware infrastructure and codegen are ready for story implementation.

---

## Phase 3: User Story 1 - Persist Enriched Group Document (Priority: P1) 🎯 MVP

**Goal**: Accept a valid submission, persist the raw payload, compute the relationship-enriched payload, upsert the processed record, and return the stored processed document.

**Independent Test**: Submit a valid micro affinity group with resolvable relationships and verify a `201` response plus one raw record in `micro-affinity-groups` and one processed record in `micro-affinity-groups-processed`.

### Tests for User Story 1

- [x] T015 [P] [US1] Add mapper unit tests in `tests/test_micro_affinity_group_relationship_mapper.py` covering one resolved outgoing relationship and destinations outside the submitted micro affinity group
- [x] T016 [P] [US1] Add endpoint success tests in `tests/test_micro_affinity_groups_endpoint.py` covering `201 Created` and the processed response body returned by `POST /micro-affinity-groups`
- [x] T017 [P] [US1] Add MongoDB integration tests in `tests/test_micro_affinity_groups_persistence.py` covering successful writes to both `micro-affinity-groups` and `micro-affinity-groups-processed`

### Implementation for User Story 1

- [x] T018 [US1] Implement `src/core/domain/micro_affinity_group_relationship_mapper.py` to transform a validated submission plus application architecture into the processed payload defined by `specs/samples/micro-affinity-group/micro-affinity-group-relationships.json`
- [x] T019 [US1] Extend `src/core/use_cases/upsert_micro_affinity_group.py` to orchestrate transaction-managed raw upsert, architecture lookup, relationship mapping, processed upsert, and processed-payload return values
- [x] T020 [US1] Update `src/adapters/inbound/api/routers/micro_affinity_groups.py` to return `src/adapters/inbound/api/schemas/micro_affinity_group_processed.py` as the success response model

**Checkpoint**: Valid submissions produce the enriched response and dual-write persistence flow end to end.

---

## Phase 4: User Story 2 - Reject Unresolvable Relationship Transformation (Priority: P2)

**Goal**: Reject relationship-resolution failures with `422`, preserve processing for workloads with zero relationships, and guarantee that processed-write failures return 500 and roll back all raw and processed writes.

**Independent Test**: Submit documents with missing architecture, missing source service, unresolved destination service, and processed-write failure conditions, then verify `422` for enrichment-resolution failures, `500` for processed-write failures, and no partial persistence.

### Tests for User Story 2

- [x] T021 [P] [US2] Add endpoint validation tests in `tests/test_micro_affinity_groups_endpoint.py` covering missing architecture, missing source service, unresolved destination service, and rejection of client-supplied `relationships`
- [x] T022 [P] [US2] Add use-case and mapper tests in `tests/test_micro_affinity_group_use_case.py` and `tests/test_micro_affinity_group_relationship_mapper.py` covering zero-relationship continuation and destination-service resolution failures
- [x] T023 [P] [US2] Add transactional rollback integration tests in `tests/test_micro_affinity_groups_persistence.py` simulating processed-write failure and asserting that the request returns 500 Internal Server Error and that both raw and processed writes are rolled back

### Implementation for User Story 2

- [x] T024 [US2] Add domain exception `src/core/exceptions/micro_affinity_group_relationship_resolution_error.py` and map it in `src/infrastructure/errors/mappers.py` and `src/infrastructure/errors/handlers.py` to `422 application/problem+json`
- [x] T025 [US2] Finalize failure-path logic and per-search logging in `src/core/domain/micro_affinity_group_relationship_mapper.py` and `src/core/use_cases/upsert_micro_affinity_group.py` for missing source-service matches, no-relationship continuation, and unresolved destination services
- [x] T026 [US2] Update `src/adapters/outbound/mongodb/transaction_manager.py`, `src/adapters/outbound/mongodb/micro_affinity_group_repository.py`, and `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py` so any write failure aborts the MongoDB transaction and leaves no partial records behind

**Checkpoint**: Invalid enrichment paths fail cleanly, workloads with zero relationships stay non-fatal, and partial writes are rolled back.

---

## Phase 5: User Story 3 - Preserve Overwrite Semantics With Enriched Content (Priority: P3)

**Goal**: Keep same-key overwrite and different-key coexistence semantics for both raw and processed records without introducing duplicate processed entries.

**Independent Test**: Submit the same valid document twice and verify one processed record remains for the composite key, then submit a variant with a different environment or architecture version and verify both processed records coexist.

### Tests for User Story 3

- [x] T027 [P] [US3] Add endpoint overwrite tests in `tests/test_micro_affinity_groups_endpoint.py` covering `200 OK` responses and recomputed processed relationships for repeated submissions with the same composite key
- [x] T028 [P] [US3] Add MongoDB integration tests in `tests/test_micro_affinity_groups_persistence.py` covering processed idempotency, same-key overwrite, and coexistence for different `environment` or `architecture-version` values

### Implementation for User Story 3

- [x] T029 [US3] Finalize full-replacement upsert semantics in `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py` and `src/core/use_cases/upsert_micro_affinity_group.py` so repeated submissions do not create duplicate processed records

**Checkpoint**: Enriched-record overwrite and coexistence behavior matches the existing endpoint semantics.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize documentation, regression coverage, and end-to-end verification across all user stories.

- [x] T030 [P] Update `README.md` and `src/adapters/inbound/api/schemas/README.md` with processed-model codegen, transaction requirements, and dual-collection persistence notes for `POST /micro-affinity-groups`
- [x] T031 [P] Update `specs/008-add-mag-relationships/quickstart.md` so the manual verification flow matches the final raw-plus-processed transactional behavior and replica-set test setup
- [x] T032 Run `./generate_inbound_models.sh`, execute the micro-affinity regression suites in `tests/test_micro_affinity_groups_endpoint.py`, `tests/test_micro_affinity_groups_persistence.py`, `tests/test_micro_affinity_group_use_case.py`, and `tests/test_micro_affinity_group_relationship_mapper.py`, and validate the manual flow documented in `specs/008-add-mag-relationships/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and establishes the processed response contract plus codegen inputs.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion and delivers the MVP enriched-response flow.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because it validates the transaction-managed transformation and error paths of the implemented endpoint.
- **User Story 3 (Phase 5)**: Depends on User Story 1 because it extends the same endpoint’s overwrite semantics for processed records.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories.
- **US2 (P2)**: Depends on US1 endpoint availability.
- **US3 (P3)**: Depends on US1 endpoint availability.

### Within Each User Story

- Tests MUST be written before or alongside implementation and fail before the final implementation passes.
- Contracts and generated response models must exist before router response changes are finalized.
- Transaction infrastructure and session-aware repository methods must exist before dual-write orchestration can pass.
- Mapper logic must exist before overwrite/idempotency semantics can be verified for processed records.

### Parallel Opportunities

- Phase 1: T003 and T004 can run in parallel after T001/T002 because they update different contract surfaces.
- Phase 2: T010 and T011 can run in parallel after T007/T008/T009 because they target different MongoDB adapters.
- Phase 3: T015, T016, and T017 can run in parallel because they target different test files.
- Phase 4: T021, T022, and T023 can run in parallel because they exercise different validation layers.
- Phase 5: T027 and T028 can run in parallel because they cover HTTP and persistence layers separately.
- Phase 6: T030 and T031 can run in parallel because they update different documentation surfaces.

---

## Parallel Example: User Story 1

```bash
# Launch the positive-path test tracks together:
Task: "Add mapper unit tests in tests/test_micro_affinity_group_relationship_mapper.py"
Task: "Add endpoint success tests in tests/test_micro_affinity_groups_endpoint.py"
Task: "Add MongoDB integration tests in tests/test_micro_affinity_groups_persistence.py"
```

---

## Parallel Example: User Story 2

```bash
# Validate transaction failure and domain failure paths in parallel:
Task: "Add endpoint validation tests in tests/test_micro_affinity_groups_endpoint.py"
Task: "Add use-case and mapper tests in tests/test_micro_affinity_group_use_case.py and tests/test_micro_affinity_group_relationship_mapper.py"
Task: "Add transactional rollback integration tests in tests/test_micro_affinity_groups_persistence.py"
```

---

## Parallel Example: User Story 3

```bash
# Verify overwrite behavior at the API and MongoDB layers in parallel:
Task: "Add endpoint overwrite tests in tests/test_micro_affinity_groups_endpoint.py"
Task: "Add MongoDB integration tests in tests/test_micro_affinity_groups_persistence.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate that one successful request writes both collections and returns the processed response

### Incremental Delivery

1. Deliver US1 for successful relationship-enriched submission
2. Add US2 to harden validation, observability, and rollback behavior
3. Add US3 to finalize processed overwrite/idempotency semantics
4. Finish with documentation and regression validation

### Parallel Team Strategy

1. One developer handles contracts/codegen while another prepares transaction ports and MongoDB adapter work
2. After Foundational completes, test work can split across mapper, endpoint, and persistence files
3. Polish tasks can run in parallel after all user stories are stable