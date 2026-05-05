---

description: "Task list for implementing 006-calm-architecture-ingest"

---

# Tasks: CALM Architecture Document Ingestion

**Input**: Design documents from `specs/006-calm-architecture-ingest/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Canonical contracts**: `schemas/calm/v1_2/calm.json`

**Authoritative service contracts/codegen inputs**: `specs/001-service-skeleton/contracts/` and `generate_inbound_models.sh`

## Phase 1: Setup (Specs-first Contracts + Codegen)

**Purpose**: Define the service contract, keep the feature working copy in sync, and generate the inbound Pydantic model.

- [X] T001 Add authoritative request schema `specs/001-service-skeleton/contracts/application_architecture.schema.json` that references `schemas/calm/v1_2/calm.json` and requires root `metadata.AssetID`, `metadata.version`, and `metadata.created`
- [X] T002 Update `specs/001-service-skeleton/contracts/openapi.yaml` to add `POST /application-architectures` with `201`/`200` success responses and `400`/`422`/`500` Problem Details
- [X] T003 [P] Update `specs/001-service-skeleton/contracts/http-api.md` to document `POST /application-architectures`, composite-key upsert semantics, and `201` vs `200` behavior
- [X] T004 [P] Sync the feature working-copy contracts in `specs/006-calm-architecture-ingest/contracts/application_architecture.schema.json`, `specs/006-calm-architecture-ingest/contracts/openapi.yaml`, and `specs/006-calm-architecture-ingest/contracts/http-api.md` with the authoritative service contract
- [X] T005 Update `generate_inbound_models.sh` to generate `src/adapters/inbound/api/schemas/application_architecture.py` from `specs/001-service-skeleton/contracts/application_architecture.schema.json`
- [X] T006 Run `./generate_inbound_models.sh` and update `src/adapters/inbound/api/schemas/README.md` to map `specs/001-service-skeleton/contracts/application_architecture.schema.json` to `src/adapters/inbound/api/schemas/application_architecture.py`

---

## Phase 2: Foundational (Ports, Use Case, Persistence Wiring)

**Purpose**: Add the core repository contract, use-case orchestration, MongoDB adapter, and DI wiring required before endpoint work.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 Add core port `src/core/ports/application_architecture_repository.py` with an upsert contract keyed by `metadata.AssetID` and `metadata.version`
- [X] T008 Add core use case `src/core/use_cases/upsert_application_architecture.py` returning a `created` result flag after extracting the composite key from validated payload metadata
- [X] T009 Implement MongoDB adapter `src/adapters/outbound/mongodb/application_architecture_repository.py` for collection `application-architectures` using `update_one({"metadata.AssetID": ..., "metadata.version": ...}, {"$set": ...}, upsert=True)` plus cleanup to preserve full-overwrite semantics
- [X] T010 Update `src/adapters/inbound/api/dependencies/wiring.py` and `src/infrastructure/main.py` to expose and register `application_architecture_repository` on app state

**Checkpoint**: Foundation ready for endpoint and validation work.

---

## Phase 3: User Story 1 - Submit a Valid CALM Document (Priority: P1) 🎯 MVP

**Goal**: Accept a valid CALM document, persist it by `AssetID + version`, and return the stored document with `201 Created` for first insert.

**Independent Test**: Submit a valid CALM document to `POST /application-architectures` and verify a `201` response plus one stored document in `application-architectures`.

### Tests for User Story 1

- [X] T011 [P] [US1] Add endpoint unit tests in `tests/test_application_architectures_endpoint.py` covering valid `POST /application-architectures` requests returning `201 Created` and the stored document when using a fake `ApplicationArchitectureRepository`
- [X] T012 [P] [US1] Add MongoDB integration tests in `tests/test_application_architectures_persistence.py` covering first-write insertion into the `application-architectures` collection and response body echo for a valid CALM document

### Implementation for User Story 1

- [X] T013 [US1] Implement `POST /application-architectures` in `src/adapters/inbound/api/routers/application_architectures.py` using `ApplicationArchitecture` and `UpsertApplicationArchitecture` with `201`/`200` status selection from the use-case result
- [X] T014 [US1] Update `src/infrastructure/main.py` to include the `application_architectures` router in the FastAPI app

**Checkpoint**: Valid CALM ingestion works end to end and is independently testable.

---

## Phase 4: User Story 2 - Reject Invalid Architecture Documents (Priority: P2)

**Goal**: Reject malformed or schema-invalid payloads before persistence with the correct `400`/`422` behavior.

**Independent Test**: Submit malformed JSON and invalid metadata payloads to `POST /application-architectures` and verify `400` or `422` responses with no record written.

### Tests for User Story 2

- [X] T015 [P] [US2] Add schema validation unit tests in `tests/test_application_architecture_validation.py` for missing root metadata, non-object metadata, invalid `AssetID`, invalid semantic `version`, and invalid `created` date values
- [X] T016 [P] [US2] Add endpoint error tests in `tests/test_application_architectures_endpoint.py` covering `422 application/problem+json` for metadata/schema failures and `400 application/problem+json` for malformed JSON

### Implementation for User Story 2

- [X] T017 [US2] Implement strict metadata validation in `src/adapters/inbound/api/schemas/application_architecture.py` so generated CALM validation is augmented with required root metadata object checks and explicit Pydantic validation for `AssetID`, `version`, and `created`

**Checkpoint**: Invalid CALM submissions are rejected before any persistence side effect.

---

## Phase 5: User Story 3 - Overwrite an Existing Architecture Version (Priority: P3)

**Goal**: Overwrite an existing document for the same `AssetID + version` while preserving separate records for different versions.

**Independent Test**: Submit a valid document twice for the same `AssetID + version` and verify the second request returns `200 OK` and overwrites the stored record; submit the same `AssetID` with a new `version` and verify both records exist.

### Tests for User Story 3

- [X] T018 [P] [US3] Add overwrite-status tests in `tests/test_application_architectures_endpoint.py` covering second-write `200 OK` for the same `AssetID + version` and `201 Created` for a different version of the same asset
- [X] T019 [P] [US3] Add MongoDB integration tests in `tests/test_application_architectures_persistence.py` verifying same-key overwrite semantics and coexistence of multiple versions for one `AssetID`

### Implementation for User Story 3

- [X] T020 [US3] Finalize overwrite semantics in `src/adapters/outbound/mongodb/application_architecture_repository.py` and `src/core/use_cases/upsert_application_architecture.py` so duplicate `AssetID + version` writes return `created=False` while different versions remain separate records

**Checkpoint**: Duplicate submissions behave deterministically and version coexistence is preserved.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize docs, schema workflow notes, and suite validation across all user stories.

- [X] T021 [P] Update `specs/006-calm-architecture-ingest/quickstart.md` so the manual verification steps match the implemented request body, statuses, and MongoDB checks
- [X] T022 [P] Update `README.md` and `src/adapters/inbound/api/schemas/README.md` with application architecture codegen and validation workflow notes
- [X] T023 Run `./generate_inbound_models.sh` and `pytest` to validate schema/model drift in `src/adapters/inbound/api/schemas/` and feature coverage in `tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and establishes contracts plus code generation.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion and delivers the MVP endpoint.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because it validates the implemented endpoint behavior.
- **User Story 3 (Phase 5)**: Depends on User Story 1 because it extends the same endpoint’s persistence semantics.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories.
- **US2 (P2)**: Depends on US1 endpoint availability.
- **US3 (P3)**: Depends on US1 endpoint availability.

### Within Each User Story

- Tests MUST be written before or alongside implementation and fail before the final implementation passes.
- Generated and validated inbound schema work must exist before router logic is finalized.
- Repository semantics must be complete before overwrite-status assertions can pass.

### Parallel Opportunities

- Phase 1: T003 and T004 can run in parallel after T001/T002 because they update different documentation files.
- Phase 3: T011 and T012 can run in parallel because they target different test files.
- Phase 4: T015 and T016 can run in parallel because they target different files and layers.
- Phase 5: T018 and T019 can run in parallel because they target different test files.
- Phase 6: T021 and T022 can run in parallel because they update different documentation surfaces.

---

## Parallel Example: User Story 1

```bash
# Launch both US1 test tracks together:
Task: "Add endpoint unit tests in tests/test_application_architectures_endpoint.py"
Task: "Add MongoDB integration tests in tests/test_application_architectures_persistence.py"
```

---

## Parallel Example: User Story 2

```bash
# Validate metadata rules at two levels in parallel:
Task: "Add schema validation unit tests in tests/test_application_architecture_validation.py"
Task: "Add endpoint error tests in tests/test_application_architectures_endpoint.py"
```

---

## Parallel Example: User Story 3

```bash
# Verify overwrite semantics through unit-level HTTP behavior and Mongo integration in parallel:
Task: "Add overwrite-status tests in tests/test_application_architectures_endpoint.py"
Task: "Add MongoDB integration tests in tests/test_application_architectures_persistence.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate the endpoint returns `201 Created` and persists one valid architecture document

### Incremental Delivery

1. Deliver US1 for valid CALM ingestion
2. Add US2 to harden validation and error classification
3. Add US3 to finalize overwrite/version coexistence behavior
4. Finish with docs and full-suite validation

### Parallel Team Strategy

1. One developer handles contract/codegen setup while another prepares foundational repository/use-case changes once the schema path is settled
2. After Foundational completes, test work can be split across endpoint and Mongo integration files
3. Polish tasks can be completed in parallel after all user stories are stable