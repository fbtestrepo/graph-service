---

description: "Task list for implementing the components echo endpoint"

---

# Tasks: Components Echo Endpoint

**Input**: Design documents from `specs/002-components-echo/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), plus `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Every task includes exact forward-slash paths in its description

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm local environment can build/run tests before making changes.

- [X] T001 Set up local dev environment per `README.md` (create `.venv`, install `requirements.txt`, install editable dev deps via `pyproject.toml`)
- [X] T002 Run baseline test suite with `pytest` from `tests/` to confirm a clean starting point

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update authoritative API contracts and boundary schemas before implementing routes.

> Note: CI/model drift checks currently use `generate_inbound_models.sh` sourced from `specs/001-service-skeleton/contracts/`, so the authoritative contract changes for this feature are applied there.

- [X] T003 Add an “any JSON value” schema in `specs/001-service-skeleton/contracts/json_value.schema.json` (accept object/array/string/number/boolean/null)
- [X] T004 [P] Update OpenAPI to include `POST /components` in `specs/001-service-skeleton/contracts/openapi.yaml` (request/response `$ref: ./json_value.schema.json`, plus `400`/`422` Problem Details)
- [X] T005 [P] Update narrative contract docs in `specs/001-service-skeleton/contracts/http-api.md` to document `POST /components` and its response/error semantics

- [X] T006 Run `./generate_inbound_models.sh` to generate `src/adapters/inbound/api/schemas/json_value.py` from `specs/001-service-skeleton/contracts/json_value.schema.json` (do not hand-edit generated output)
- [X] T007 [P] Update `src/adapters/inbound/api/schemas/README.md` to document `json_value.py` as generated from `specs/001-service-skeleton/contracts/json_value.schema.json`

**Checkpoint**: Contracts + inbound schema exist; router work can begin.

---

## Phase 3: User Story 1 — Echo any JSON payload (Priority: P1) 🎯 MVP

**Goal**: `POST /components` accepts any valid JSON value, echoes it back with `200 OK`, and logs the payload (log representation truncated to first 4096 characters with truncation indicated).

**Independent Test**: Using `TestClient` in `tests/`, send object JSON and array JSON to `POST /components` and verify response status `200` and response JSON equals the request JSON.

### Tests for User Story 1

- [X] T008 [US1] Add object-JSON echo test for `POST /components` in `tests/test_components_endpoint.py`
- [X] T009 [US1] Add array-JSON echo test for `POST /components` in `tests/test_components_endpoint.py`

### Implementation for User Story 1

- [X] T010 [US1] Implement `POST /components` handler in `src/adapters/inbound/api/routers/components.py` using `src/adapters/inbound/api/schemas/json_value.py` as the request body type and echoing the parsed JSON in the response
- [X] T011 [US1] Add request logging in `src/adapters/inbound/api/routers/components.py` (serialize payload, truncate log representation to first 4096 characters, and indicate truncation; log exactly once per request)
- [X] T012 [US1] Run `pytest -k components` against `tests/` to validate US1 behavior

**Checkpoint**: `POST /components` works end-to-end for valid JSON.

---

## Phase 4: User Story 2 — Invalid JSON returns a clear error (Priority: P2)

**Goal**: Malformed JSON request bodies return `400` with RFC7807 Problem Details (`application/problem+json`).

**Independent Test**: Send a malformed JSON body to `POST /components` and verify `400` and `Content-Type: application/problem+json`.

### Tests for User Story 2

- [X] T013 [US2] Add malformed-JSON test for `POST /components` in `tests/test_components_endpoint.py` (send invalid JSON bytes with `content-type: application/json`; assert `400` and problem-details content type)
- [X] T018 [US2] Add missing-body test for `POST /components` in `tests/test_components_endpoint.py` (omit request body; assert `422` and `Content-Type: application/problem+json`)

### Implementation for User Story 2

- [X] T014 [US2] Verify `src/infrastructure/errors/validation.py` maps malformed JSON to `400` (no code changes expected); adjust only if the new endpoint reveals a gap

**Checkpoint**: Malformed JSON yields consistent `400` Problem Details.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Ensure repo guardrails and quickstart validation pass.

- [X] T015 Run schema/model drift checks via `./generate_inbound_models.sh` and validate no diffs under `src/adapters/inbound/api/schemas/`
- [X] T016 Run core purity guardrail via `python check_core_purity.py`
- [X] T017 Validate the manual verification steps in `specs/002-components-echo/quickstart.md` (run `uvicorn ...` and the `curl` examples)

---

## Dependencies & Execution Order

### User Story Completion Order (Dependency Graph)

- Setup (Phase 1) → Foundational (Phase 2) → US1 (Phase 3) → US2 (Phase 4) → Polish (Phase 5)

### Within Each User Story

- Tests (T008–T009, T013) should be written first and fail before implementation changes in `src/`
- Contracts + schemas (Phase 2) must land before route implementation (T010–T011)

---

## Parallel Execution Examples (by story)

### Foundational parallel examples

- T004 in `specs/001-service-skeleton/contracts/openapi.yaml` can be done in parallel with T005 in `specs/001-service-skeleton/contracts/http-api.md`
- T006 (run `./generate_inbound_models.sh`) can be done in parallel with T007 in `src/adapters/inbound/api/schemas/README.md`

### US1 parallel examples

- US1 test tasks are intentionally in the same file (`tests/test_components_endpoint.py`) and should be done sequentially to avoid merge conflicts

### US2 parallel examples

- T013 in `tests/test_components_endpoint.py` can be done in parallel with Phase 5 verification tasks (e.g., T016 `python check_core_purity.py`) since it does not depend on them

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1 → Phase 2
2. Complete US1 (Phase 3)
3. Stop and validate `POST /components` echo behavior with tests in `tests/`

### Incremental Delivery

- Implement US1 first (valid JSON echo)
- Then add US2 (malformed JSON behavior) and re-validate

---

## Notes

- The spec and research define truncation for **logging only**; the HTTP response body must remain a valid JSON value equal to the submitted JSON.
- If product intent changes to “truncate the HTTP response payload to 4096 characters", update `specs/002-components-echo/spec.md` and revise the API contract to define a new, JSON-valid response shape.
