---

description: "Task list for implementing the service architectural skeleton"
---

# Tasks: Service Architectural Skeleton

**Input**: Design documents from `specs/001-service-skeleton/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), plus `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Every task includes exact forward-slash paths in its description

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the baseline repository structure and Python project metadata.

- [x] T001 Create baseline Python packages and directory tree by adding `__init__.py` files under `src/` and `tests/` (e.g., `src/__init__.py`, `src/core/__init__.py`, `src/core/domain/__init__.py`, `src/core/ports/__init__.py`, `src/core/use_cases/__init__.py`, `src/core/exceptions/__init__.py`, `src/adapters/__init__.py`, `src/adapters/inbound/__init__.py`, `src/adapters/inbound/api/__init__.py`, `src/adapters/inbound/api/dependencies/__init__.py`, `src/adapters/inbound/api/routers/__init__.py`, `src/adapters/inbound/api/schemas/__init__.py`, `src/adapters/outbound/__init__.py`, `src/adapters/outbound/mongodb/__init__.py`, `src/adapters/outbound/ldap/__init__.py`, `src/infrastructure/__init__.py`, `src/infrastructure/config/__init__.py`, `src/infrastructure/errors/__init__.py`, `src/infrastructure/middleware/__init__.py`, `tests/__init__.py`)
- [x] T002 Initialize Python project metadata and runtime dependencies in `pyproject.toml` (Python 3.12, FastAPI, Pydantic, PyMongo, LDAP3, pytest) and generate a pinned `requirements.txt` lockfile (e.g., add `pip-tools` as a dev dependency and run `pip-compile` to produce `requirements.txt`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core wiring and quality gates that must exist before user stories can be implemented safely.

- [x] T003 [P] Add runtime settings model in `src/infrastructure/config/settings.py` (MongoDB Atlas + LDAP settings placeholders; no secrets committed)
- [x] T004 Create FastAPI application factory in `src/infrastructure/main.py` (`create_app()`), with startup/shutdown hooks and router/handler registration points
- [x] T005 [P] Add DI helper functions in `src/adapters/inbound/api/dependencies/wiring.py` (read adapters/clients from `app.state` without importing outbound adapters in core)
- [x] T006 [P] Add core purity check script in `check_core_purity.py` (fails if any file under `src/core/` imports forbidden libraries like `fastapi`, `motor`, `pymongo`, `ldap3`)
- [x] T007 [P] Add CI workflow skeleton in `.github/workflows/ci.yml` to run `python -m compileall src`, `python check_core_purity.py`, and `pytest`

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 — Scaffold the baseline structure (Priority: P1) 🎯 MVP

**Goal**: Provide the complete baseline directory structure plus minimal composition points, with a working health endpoint.

**Independent Test**: Import `src/infrastructure/main.py` and call `create_app()`, then call `GET /health` and verify `200` with `status: ok`.

### Implementation for User Story 1

- [x] T008 [P] [US1] Create core domain entities in `src/core/domain/component.py`, `src/core/domain/dependency_edge.py`, and `src/core/domain/dependency_graph.py`
- [x] T009 [P] [US1] Create representative domain exceptions in `src/core/exceptions/component_not_found.py`, `src/core/exceptions/circular_dependency_detected.py`, `src/core/exceptions/duplicate_dependency_edge.py`, `src/core/exceptions/authentication_failed.py`, and `src/core/exceptions/authorization_denied.py`
- [x] T010 [P] [US1] Define graph persistence port ABC in `src/core/ports/graph_repository.py` (include at least a `get_component(component_id: str)` method returning an optional component)
- [x] T011 [P] [US1] Define identity provider port ABC in `src/core/ports/identity_provider.py` with synchronous methods and explicit failure semantics: authentication failures MUST raise `AuthenticationFailed` (maps to 401) and authorization failures MUST raise `AuthorizationDenied` (maps to 403); no FastAPI/LDAP imports
- [x] T012 [P] [US1] Scaffold MongoDB outbound adapter skeleton in `src/adapters/outbound/mongodb/client.py` and `src/adapters/outbound/mongodb/graph_repository.py` (PyMongo client creation + stub port implementation; adapter methods remain synchronous to match core ports)
- [x] T013 [P] [US1] Scaffold LDAP outbound adapter skeleton in `src/adapters/outbound/ldap/client.py` and `src/adapters/outbound/ldap/identity_provider.py` (LDAP3 connection creation + stub port implementation; translate LDAP bind failures to `AuthenticationFailed` and role/permission failures to `AuthorizationDenied`)
- [x] T014 [US1] Wire app-singleton outbound adapters into `src/infrastructure/main.py` startup/shutdown and expose them via `app.state` for DI in `src/adapters/inbound/api/dependencies/wiring.py`
- [x] T015 [P] [US1] Add health response model in `src/adapters/inbound/api/schemas/health_response.py` (temporary until US2 generation; must match `specs/001-service-skeleton/contracts/health_response.schema.json`)
- [x] T016 [US1] Implement health router in `src/adapters/inbound/api/routers/health.py` and register it in `src/infrastructure/main.py` (route: `GET /health`, response model: `HealthResponse`)

**Checkpoint**: MVP endpoints and wiring exist; repository structure is stable.

---

## Phase 4: User Story 2 — Enforce specs-first validation at the boundary (Priority: P2)

**Goal**: Ensure request validation happens at the inbound boundary based on `specs/` schemas, and validation failures return RFC 7807 Problem Details.

**Independent Test**:
- Send a syntactically invalid JSON body (malformed/unparseable) and verify a `400` Problem Details response with `Content-Type: application/problem+json`
- Send a syntactically valid JSON body that violates schema constraints and verify a `422` Problem Details response with `Content-Type: application/problem+json`
- In both cases, verify the core use case is not invoked

### Implementation for User Story 2

- [x] T017 [US2] Define the request schema in `specs/001-service-skeleton/contracts/component.schema.json` for the validation endpoint and keep `specs/001-service-skeleton/contracts/http-api.md` consistent with the authoritative artifacts
- [x] T018 [P] [US2] Add source-of-truth JSON Schemas under `specs/001-service-skeleton/contracts/` (e.g., `health_response.schema.json`, `problem_details.schema.json`)
- [x] T019 [US2] Add OpenAPI skeleton in `specs/001-service-skeleton/contracts/openapi.yaml` referencing the JSON Schemas for `GET /health` and the validation endpoint
- [x] T020 [US2] Add codegen dependency configuration in `pyproject.toml` for generating Pydantic models from JSON Schema (e.g., `datamodel-code-generator` in a dev dependency group)
- [x] T021 [US2] Generate and commit inbound Pydantic models in `src/adapters/inbound/api/schemas/component.py`, `src/adapters/inbound/api/schemas/problem_details.py`, and `src/adapters/inbound/api/schemas/health_response.py` from the JSON Schemas in `specs/001-service-skeleton/contracts/`
- [x] T022 [US2] Add schema-to-model mapping notes in `src/adapters/inbound/api/schemas/README.md` (list each generated model and its schema source path)
- [x] T023 [US2] Implement validation error handling in `src/infrastructure/errors/validation.py` to convert inbound validation failures into RFC 7807 Problem Details using `src/adapters/inbound/api/schemas/problem_details.py`, returning `400` for malformed/unparseable JSON and `422` for schema/constraint violations

- [x] T024 [US2] Register the validation error handler in `src/infrastructure/main.py` so invalid request payloads return `application/problem+json`
- [x] T025 [US2] Implement the validation endpoint in `src/adapters/inbound/api/routers/component_validation.py` using the generated `Component` model as the request body schema
- [x] T026 [US2] Add model generation script at `generate_inbound_models.sh` (regenerates `src/adapters/inbound/api/schemas/component.py`, `src/adapters/inbound/api/schemas/problem_details.py`, and `src/adapters/inbound/api/schemas/health_response.py` from the JSON Schemas)
- [x] T027 [US2] Update `.github/workflows/ci.yml` to run `./generate_inbound_models.sh` and fail if `git diff --exit-code src/adapters/inbound/api/schemas` is non-empty (schema/model drift check)

**Checkpoint**: Specs-first validation mechanism is in place and enforced by CI.

---

## Phase 5: User Story 3 — Standardize error responses via global handlers (Priority: P3)

**Goal**: Map domain exceptions to semantically correct HTTP responses and return sanitized RFC 7807 Problem Details.

**Independent Test**: Trigger a core domain exception via an API call and verify the handler returns the correct status code and Problem Details without stack traces.

### Implementation for User Story 3

- [x] T028 [P] [US3] Add Problem Details response helpers in `src/infrastructure/errors/problem_details.py` (construct Problem Details consistently; set `Content-Type: application/problem+json`)


- [x] T029 [P] [US3] Add domain-exception-to-HTTP mapping in `src/infrastructure/errors/mappers.py` (e.g., `ComponentNotFound` → 404, `DuplicateDependencyEdge` → 409, `CircularDependencyDetected` → 409, `AuthenticationFailed` → 401, `AuthorizationDenied` → 403)

- [x] T030 [US3] Implement global exception handlers in `src/infrastructure/errors/handlers.py` for (a) domain exceptions, (b) `starlette.exceptions.HTTPException` / `fastapi.HTTPException` (e.g., 404/405 and explicit `raise HTTPException(...)`), and (c) fallback 500, returning RFC 7807 Problem Details and never leaking stack traces

- [x] T031 [US3] Register global exception handlers in `src/infrastructure/main.py`
- [x] T032 [P] [US3] Implement a minimal core use case in `src/core/use_cases/get_component.py` that uses `src/core/ports/graph_repository.py` and raises `ComponentNotFound` when missing
- [x] T033 [US3] Add a minimal endpoint in `src/adapters/inbound/api/routers/components.py` that calls the `GetComponent` use case and demonstrates domain exception mapping (e.g., `GET /components/{component_id}`)
- [x] T034 [US3] Update `specs/001-service-skeleton/contracts/http-api.md` and `specs/001-service-skeleton/contracts/openapi.yaml` to include `GET /components/{component_id}` and its error responses as Problem Details

**Checkpoint**: Domain exceptions are consistently mapped to RFC 7807 responses.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish documentation and ensure the quickstart is executable.

- [x] T035 [P] Update `specs/001-service-skeleton/quickstart.md` with the concrete run command and required env var names once `src/infrastructure/config/settings.py` is implemented
- [x] T036 [P] Document developer workflow notes in `README.md` (how to run `pytest`, how to run `generate_inbound_models.sh`, and what CI enforces)

---

## Dependencies & Execution Order

- **Setup (Phase 1)**: Start immediately
- **Foundational (Phase 2)**: Depends on Setup; blocks all user story phases
- **US1 (Phase 3)**: Depends on Foundational; delivers MVP (`GET /health`)
- **US2 (Phase 4)**: Depends on US1 (router skeleton + schemas folder exists); adds specs-first validation + drift checks
- **US3 (Phase 5)**: Depends on US2 (Problem Details model exists) and US1 (core exceptions/ports exist)
- **Polish (Phase 6)**: Depends on desired user stories being complete

## Parallel Execution Examples (by story)

### US1 parallel examples

- Implement core domain entities in `src/core/domain/component.py` and `src/core/domain/dependency_edge.py` in parallel
- Implement port interfaces in `src/core/ports/graph_repository.py` and `src/core/ports/identity_provider.py` in parallel
- Scaffold outbound adapters in `src/adapters/outbound/mongodb/graph_repository.py` and `src/adapters/outbound/ldap/identity_provider.py` in parallel

### US2 parallel examples

- Write JSON Schemas in `specs/001-service-skeleton/contracts/component.schema.json` and `specs/001-service-skeleton/contracts/problem_details.schema.json` in parallel
- Implement `src/infrastructure/errors/validation.py` while generating `src/adapters/inbound/api/schemas/component.py`

### US3 parallel examples

- Implement mapping in `src/infrastructure/errors/mappers.py` while implementing the use case in `src/core/use_cases/get_component.py`

## Implementation Strategy

- **MVP first**: Complete Phase 1 → Phase 2 → US1, then validate `GET /health` end-to-end.
- **Incremental delivery**: Add US2 (validation + drift checks) next, then US3 (domain error mapping), validating after each checkpoint.
