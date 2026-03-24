# Tasks: Persist Components Payload

**Input**: Design documents from `specs/003-persist-components-payload/`

- Required: `specs/003-persist-components-payload/spec.md`, `specs/003-persist-components-payload/plan.md`
- Optional (available):
  - `specs/003-persist-components-payload/research.md`
  - `specs/003-persist-components-payload/data-model.md`
  - `specs/003-persist-components-payload/contracts/`
  - `specs/003-persist-components-payload/quickstart.md`

**Tests**: REQUIRED by spec (**FR-007**) and must run MongoDB locally (Docker/testcontainers).

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare dependencies and contracts-first updates that unblock implementation.

- [ ] T001 Add `testcontainers[mongodb]` to `pyproject.toml` under `[project.optional-dependencies].dev`
- [x] T001 Add `testcontainers[mongodb]` to `pyproject.toml` under `[project.optional-dependencies].dev`
- [x] T002 [P] Add MongoDB testcontainer fixtures in `tests/conftest.py` (start MongoDB container, set `GRAPH_SERVICE_MONGODB_URI`/`GRAPH_SERVICE_MONGODB_DATABASE` before `create_app()`)
- [x] T003 [P] Update `specs/001-service-skeleton/contracts/openapi.yaml` to document `500 application/problem+json` for `POST /components` and update the summary to mention persistence
- [x] T004 [P] Update `specs/001-service-skeleton/contracts/http-api.md` to document persistence as a side effect of `POST /components` success and to document `500 application/problem+json` on persistence failure
- [x] T005 Run `generate_inbound_models.sh` and ensure no drift in `src/adapters/inbound/api/schemas/` after the contract changes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Introduce the core port and MongoDB adapter needed by both user stories.

- [x] T006 Create core domain model `src/core/domain/component_payload_record.py` defining `ComponentPayloadRecord(received_at, payload)`
- [x] T007 Define port ABC in `src/core/ports/component_payload_repository.py` for persisting `ComponentPayloadRecord` (no MongoDB/PyMongo imports in core)
- [x] T008 Implement use case `src/core/use_cases/record_component_payload.py` to create `ComponentPayloadRecord` with `received_at=UTC now`, call the port, and return the original payload for echo
- [x] T009 Implement MongoDB adapter `src/adapters/outbound/mongodb/component_payload_repository.py` to insert documents into the `component_payload_records` collection with fields `received_at` and `payload`
- [x] T010 Wire the adapter in `src/infrastructure/main.py` startup and expose it via `app.state.component_payload_repository`
- [x] T011 Add FastAPI dependency getter `get_component_payload_repository()` in `src/adapters/inbound/api/dependencies/wiring.py`

**Checkpoint**: The service can obtain a payload repository from DI and the core can persist records via a port.

---

## Phase 3: User Story 1 — Persist echoed payloads (Priority: P1) 🎯 MVP

**Goal**: Every successful `POST /components` request is persisted to MongoDB before returning `200`, while still echoing the JSON unchanged (including non-object roots).

**Independent Test**: With MongoDB available, send both an object and a non-object JSON value to `POST /components`, receive `200` with an identical echo body, and verify a new DB record exists with matching `payload`.

### Tests (REQUIRED)

- [x] T012 [P] [US1] Add integration tests in `tests/test_components_persistence.py` to persist+echo an object JSON payload and a non-object JSON payload, asserting an inserted record exists with matching `payload` and a present `received_at`

### Implementation

- [x] T013 [US1] Update `src/adapters/inbound/api/routers/components.py` to depend on `get_component_payload_repository`, invoke `RecordComponentPayload`, and ensure persistence happens before returning the `200` echo response

**Checkpoint**: US1 complete when T012 passes and `POST /components` persists + echoes for object and non-object JSON.

---

## Phase 4: User Story 2 — Persistence failure is explicit (Priority: P2)

**Goal**: If persistence fails for any reason, `POST /components` returns `500 application/problem+json` and MUST NOT return `200`.

**Independent Test**: Configure the service to use an unavailable MongoDB URI and verify `POST /components` returns a problem-details `500` response.

### Tests

- [x] T014 [P] [US2] Add integration test in `tests/test_components_persistence_failure.py` that sets `GRAPH_SERVICE_MONGODB_URI` to an unavailable endpoint and asserts `POST /components` returns `500` with `application/problem+json` (use `TestClient(..., raise_server_exceptions=False)` if needed)

### Implementation

- [x] T015 [US2] Ensure `src/adapters/inbound/api/routers/components.py` does not swallow persistence exceptions and that the global handler in `src/infrastructure/errors/handlers.py` produces a `500 application/problem+json` response

**Checkpoint**: US2 complete when T014 passes and the service never reports false `200` on persistence failure.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and guardrails.

- [ ] T016 Validate the manual verification steps in `specs/003-persist-components-payload/quickstart.md` still work end-to-end (Docker Mongo + curl + mongosh)
- [x] T017 Run the full test suite (`pytest`) and ensure all tests under `tests/` pass
- [x] T018 Run `check_core_purity.py` and ensure the new core files do not import forbidden libraries

---

## Dependencies & Execution Order

- Phase 1 (Setup) → Phase 2 (Foundational) → US1 (P1) → US2 (P2) → Polish
- US2 depends on US1’s foundational persistence wiring (same endpoint, same port/adapter).

## Parallel Opportunities

- Phase 1: T002, T003, and T004 can be done in parallel.
- US1 tests (T012) can be written in parallel with the core/adapter wiring once T001/T002 exist.

## Parallel Example: User Story 1

- T012 [US1] in `tests/test_components_persistence.py`
- T013 [US1] in `src/adapters/inbound/api/routers/components.py`

## Implementation Strategy

- MVP first: complete Phase 1 + Phase 2 + US1, then stop and validate persistence with both object and non-object JSON.
- Then add US2 failure behavior and validate `500 application/problem+json` for unavailable MongoDB.
