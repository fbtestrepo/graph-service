---

description: "Task list for implementing 007-add-micro-affinity-endpoint"

---

# Tasks: Micro Affinity Group Submission

**Input**: Design documents from `specs/007-add-micro-affinity-endpoint/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Authoritative service contracts/codegen inputs**: `specs/001-service-skeleton/contracts/` and `generate_inbound_models.sh`

## Phase 1: Setup (Specs-first Contracts + Codegen)

**Purpose**: Define the authoritative service contract, keep the feature working copy aligned, and generate the inbound Pydantic schema.

- [x] T001 Add authoritative request schema `specs/001-service-skeleton/contracts/micro_affinity_group.schema.json` from the feature contract in `specs/007-add-micro-affinity-endpoint/contracts/micro_affinity_group.schema.json`
- [x] T002 Update `specs/001-service-skeleton/contracts/openapi.yaml` to add `POST /micro-affinity-groups` with `201`/`200` success responses and `400`/`422`/`500` Problem Details
- [x] T003 [P] Update `specs/001-service-skeleton/contracts/http-api.md` to document `POST /micro-affinity-groups`, unique-key upsert semantics, and `201` vs `200` behavior
- [x] T004 [P] Sync the feature working-copy contracts in `specs/007-add-micro-affinity-endpoint/contracts/http-api.md`, `specs/007-add-micro-affinity-endpoint/contracts/openapi.yaml`, and `specs/007-add-micro-affinity-endpoint/contracts/micro_affinity_group.schema.json` with the authoritative service contract
- [x] T005 Update `generate_inbound_models.sh` to generate `src/adapters/inbound/api/schemas/micro_affinity_group.py` from `specs/001-service-skeleton/contracts/micro_affinity_group.schema.json` and append a stable wrapper model for feature-specific validators
- [x] T006 Run `./generate_inbound_models.sh` and update `src/adapters/inbound/api/schemas/README.md` to map `specs/001-service-skeleton/contracts/micro_affinity_group.schema.json` to `src/adapters/inbound/api/schemas/micro_affinity_group.py`

---

## Phase 2: Foundational (Ports, Persistence, Wiring)

**Purpose**: Add the reusable core ports, MongoDB adapters, and DI wiring required before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Extend `src/core/ports/application_architecture_repository.py` with a lookup contract for reading one architecture document by `metadata.AssetID` and `metadata.version`
- [x] T008 Add core port `src/core/ports/micro_affinity_group_repository.py` with an upsert contract keyed by `micro-ag-id`, `environment`, and `architecture-version`
- [x] T009 Implement architecture lookup support in `src/adapters/outbound/mongodb/application_architecture_repository.py` so the feature can load one matching architecture payload for validation
- [x] T010 Implement `src/adapters/outbound/mongodb/micro_affinity_group_repository.py` for collection `micro-affinity-groups` with full-overwrite upsert semantics and created-vs-updated detection
- [x] T011 Add the core result type and use-case skeleton in `src/core/use_cases/upsert_micro_affinity_group.py`, including constructor dependencies and execute signature, without workload-alignment business rules
- [x] T012 [P] Update `src/adapters/inbound/api/dependencies/wiring.py` and `src/infrastructure/main.py` to expose and register `micro_affinity_group_repository` plus the extended `application_architecture_repository`

**Checkpoint**: Foundation ready for endpoint and validation work.

---

## Phase 3: User Story 1 - Submit a Valid Micro Affinity Group (Priority: P1) 🎯 MVP

**Goal**: Accept a valid micro affinity group document, validate its workloads against the matching application architecture, persist it, and return `201 Created` for a first insert.

**Independent Test**: Submit a valid document to `POST /micro-affinity-groups` with a matching application architecture record present and verify a `201` response plus one stored document in `micro-affinity-groups`.

### Tests for User Story 1

- [x] T013 [P] [US1] Add endpoint success tests in `tests/test_micro_affinity_groups_endpoint.py` covering first valid `POST /micro-affinity-groups` requests returning `201 Created` and acceptance of omitted `name` when fake repositories provide a matching architecture record
- [x] T014 [P] [US1] Add MongoDB integration tests in `tests/test_micro_affinity_groups_persistence.py` covering first-write insertion into the `micro-affinity-groups` collection for a valid request with a matching stored application architecture

### Implementation for User Story 1

- [x] T015 [US1] Implement the positive-path execute logic in `src/core/use_cases/upsert_micro_affinity_group.py` using architecture lookup, service-node resolution by `metadata.code-repo`, resolved service node `metadata.asset-id` to submitted `workload.asset-id` verification, and successful upsert result handling
- [x] T016 [US1] Implement `POST /micro-affinity-groups` in `src/adapters/inbound/api/routers/micro_affinity_groups.py` using `MicroAffinityGroup` from `src/adapters/inbound/api/schemas/micro_affinity_group.py` and `UpsertMicroAffinityGroup`
- [x] T017 [US1] Update `src/infrastructure/main.py` to include the `micro_affinity_groups` router in the FastAPI app

**Checkpoint**: Valid micro affinity group submission works end to end and is independently testable.

---

## Phase 4: User Story 2 - Reject Invalid or Unresolvable Documents (Priority: P2)

**Goal**: Reject malformed, schema-invalid, or architecture-mismatched submissions with the required `400`/`422` behavior and no persistence side effects.

**Independent Test**: Submit malformed JSON, invalid semver/timestamp payloads, duplicate or empty workloads, missing architecture records, repo mismatches, and asset-id mismatches to `POST /micro-affinity-groups` and verify `400` or `422` responses with no stored record.

### Tests for User Story 2

- [x] T018 [P] [US2] Add request-validation tests in `tests/test_micro_affinity_groups_endpoint.py` covering malformed JSON, invalid `architecture-version`, invalid `effective-date`, unknown fields, duplicate workload IDs, empty workloads, and wrong payload types
- [x] T019 [P] [US2] Add domain-validation tests in `tests/test_micro_affinity_group_use_case.py` and endpoint error cases in `tests/test_micro_affinity_groups_endpoint.py` covering missing architecture records, missing `service` node matches by `metadata.code-repo`, and submitted `workload.asset-id` to resolved service node `metadata.asset-id` mismatches

### Implementation for User Story 2

- [x] T020 [US2] Finalize inbound validators in `src/adapters/inbound/api/schemas/micro_affinity_group.py` and the appended wrapper logic in `generate_inbound_models.sh` so exact timestamp, non-empty workloads, duplicate `workload.id`, and closed-shape rules fail before the core use case runs
- [x] T021 [US2] Add domain exceptions `src/core/exceptions/application_architecture_not_found.py` and `src/core/exceptions/micro_affinity_group_workload_mismatch.py` and map them in `src/infrastructure/errors/mappers.py` and `src/infrastructure/errors/handlers.py` to `422 application/problem+json`
- [x] T022 [US2] Complete failure-path validation in `src/core/use_cases/upsert_micro_affinity_group.py` so missing architecture documents, missing `service` node repo matches, and resolved service node `metadata.asset-id` to submitted `workload.asset-id` mismatches raise the mapped domain exceptions

**Checkpoint**: Invalid and unresolvable submissions are rejected before any persistence side effect.

---

## Phase 5: User Story 3 - Overwrite a Matching Existing Record (Priority: P3)

**Goal**: Overwrite an existing document for the same `micro-ag-id + environment + architecture-version` while preserving separate records for different environments or architecture versions.

**Independent Test**: Submit a valid document twice for the same unique key and verify the second request returns `200 OK` and overwrites the stored document; submit a different environment or architecture version and verify both records exist.

### Tests for User Story 3

- [x] T023 [P] [US3] Add endpoint overwrite and coexistence tests in `tests/test_micro_affinity_groups_endpoint.py` covering second-write `200 OK` for the same unique key and separate persistence for different `environment` or `architecture-version` values
- [x] T024 [P] [US3] Add MongoDB integration tests in `tests/test_micro_affinity_groups_persistence.py` verifying same-key overwrite semantics and coexistence of multiple records when either `environment` or `architecture-version` differs

### Implementation for User Story 3

- [x] T025 [US3] Finalize full-overwrite semantics and created-vs-updated detection in `src/adapters/outbound/mongodb/micro_affinity_group_repository.py` and `src/core/use_cases/upsert_micro_affinity_group.py` so duplicate-key writes return `created=False` without leaving stale fields behind

**Checkpoint**: Duplicate submissions behave deterministically and separate key variants coexist.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize documentation, codegen guidance, and suite validation across all user stories.

- [x] T026 [P] Update `specs/007-add-micro-affinity-endpoint/quickstart.md` so the manual verification steps match the final authoritative contract path, seeded architecture shape, and endpoint behavior
- [x] T027 [P] Update `README.md` and `src/adapters/inbound/api/schemas/README.md` with micro-affinity-group codegen, validation, and testing workflow notes
- [x] T028 Run `./generate_inbound_models.sh` and `pytest` for the micro-affinity-group functional suites to validate schema/model drift and end-to-end feature coverage
- [x] T029 Add a sequential performance smoke test for POST /micro-affinity-groups, following the existing performance-smoke pattern, that submits a valid payload up to 250 KB 100 times and asserts at least 95 requests complete within 2 seconds in the test environment
---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and establishes authoritative contracts plus code generation.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion and delivers the MVP endpoint.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because it validates the implemented endpoint and use-case failure paths.
- **User Story 3 (Phase 5)**: Depends on User Story 1 because it extends the same endpoint’s persistence semantics.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories.
- **US2 (P2)**: Depends on US1 endpoint availability.
- **US3 (P3)**: Depends on US1 endpoint availability.

### Within Each User Story

- Tests MUST be written before or alongside implementation and fail before the final implementation passes.
- Contracts and generated schema code must exist before router logic is finalized.
- Repository lookup and upsert behavior must exist before positive-path orchestration can pass.
- Domain exceptions and error mapping must be complete before endpoint-level `422` assertions can pass.

### Parallel Opportunities

- Phase 1: T003 and T004 can run in parallel after T001/T002 because they update different contract documentation files.
- Phase 2: T009 and T010 can run in parallel after T007/T008 because they target different adapters.
- Phase 3: T013 and T014 can run in parallel because they target different test files.
- Phase 4: T018 and T019 can run in parallel because they target different validation layers and files.
- Phase 5: T023 and T024 can run in parallel because they target different test files.
- Phase 6: T026 and T027 can run in parallel because they update different documentation surfaces.

---

## Parallel Example: User Story 1

```bash
# Launch both US1 test tracks together:
Task: "Add endpoint success tests in tests/test_micro_affinity_groups_endpoint.py"
Task: "Add MongoDB integration tests in tests/test_micro_affinity_groups_persistence.py"
```

---

## Parallel Example: User Story 2

```bash
# Validate request-shape failures and domain-alignment failures in parallel:
Task: "Add request-validation tests in tests/test_micro_affinity_groups_endpoint.py"
Task: "Add domain-validation tests in tests/test_micro_affinity_group_use_case.py and tests/test_micro_affinity_groups_endpoint.py"
```

---

## Parallel Example: User Story 3

```bash
# Verify overwrite behavior at the HTTP and MongoDB layers in parallel:
Task: "Add endpoint overwrite and coexistence tests in tests/test_micro_affinity_groups_endpoint.py"
Task: "Add MongoDB integration tests in tests/test_micro_affinity_groups_persistence.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate the endpoint returns `201 Created` and persists one valid micro affinity group document

### Incremental Delivery

1. Deliver US1 for valid micro affinity group ingestion
2. Add US2 to harden validation and cross-collection error classification
3. Add US3 to finalize overwrite and coexistence behavior
4. Finish with documentation and full-suite validation

### Parallel Team Strategy

1. One developer handles contract/codegen setup while another prepares repository ports and adapter work once the authoritative schema path is settled
2. After Foundational completes, test work can be split across endpoint, use-case, and MongoDB integration files
3. Polish tasks can be completed in parallel after all user stories are stable