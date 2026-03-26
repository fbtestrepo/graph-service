---

description: "Task list for implementing 004-components-payload-schema"

---

# Tasks: Components Payload Validation & MongoDB Upsert

**Input**: Design documents from `specs/004-components-payload-schema/` (plan.md, spec.md, data-model.md, research.md, contracts/)

**Authoritative contracts**: `specs/001-service-skeleton/contracts/` (used by `generate_inbound_models.sh`)

## Phase 1: Setup (Specs-first Contracts + Codegen)

**Purpose**: Make contracts authoritative and generate inbound Pydantic models.

- [x] T001 Add JSON Schema `specs/001-service-skeleton/contracts/component_node.schema.json` (copy from `specs/004-components-payload-schema/contracts/component_node.schema.json`)
- [x] T002 Update OpenAPI `specs/001-service-skeleton/contracts/openapi.yaml` to define `POST /components` request/200/201 responses using `component_node.schema.json` and to update `GET /components/{component_id}` response to `component_node.schema.json` (treat `{component_id}` as `node-id`)
- [x] T003 [P] Update `specs/001-service-skeleton/contracts/http-api.md` to describe `POST /components` upsert-by-`node-id` and the updated `GET /components/{component_id}` semantics/response shape
- [x] T004 Update the working-copy contracts: `specs/004-components-payload-schema/contracts/openapi.yaml` and `specs/004-components-payload-schema/contracts/http-api.md` so `GET /components/{component_id}` returns/declares `component_node.schema.json` (keep working copy consistent with spec)
- [x] T005 Update codegen script `generate_inbound_models.sh` to generate `src/adapters/inbound/api/schemas/component_node.py` from `specs/001-service-skeleton/contracts/component_node.schema.json`
- [x] T006 Run `./generate_inbound_models.sh` and verify the generated model `src/adapters/inbound/api/schemas/component_node.py` forbids unknown fields except under `metadata` (and that imports/formatting remain valid)

---

## Phase 2: Foundational (Ports, Use Cases, Outbound Adapter, Wiring)

**Purpose**: Introduce a core port + Mongo adapter for upserting and reading component-node documents.

- [x] T007 Define core port `src/core/ports/component_node_repository.py` with methods for upsert-by-`node-id` (return created-vs-updated) and get-by-`node-id` (return stored payload)
- [x] T008 Implement core use case `src/core/use_cases/upsert_component_node.py` to call the port and return an upsert result (created vs updated)
- [x] T009 Implement core use case `src/core/use_cases/get_component_node.py` to load by `node-id` and raise `src/core/exceptions/component_not_found.py` when missing
- [x] T010 Implement Mongo adapter `src/adapters/outbound/mongodb/component_node_repository.py` using the `components` collection with `replace_one(filter={"node-id": node_id}, replacement=payload, upsert=True)` and `find_one({"node-id": node_id})`
- [x] T011 Wire the repository in `src/infrastructure/main.py` by creating/storing `app.state.component_node_repository` on startup
- [x] T012 [P] Expose DI provider `get_component_node_repository` in `src/adapters/inbound/api/dependencies/wiring.py`

---

## Phase 3: User Story 1 — Upsert a Component (Priority: P1) 🎯 MVP

**Goal**: Accept a valid component-node payload, upsert it by `node-id`, return `201` on create and `200` on update, and support retrieval via `GET /components/{component_id}` (where `{component_id}` is treated as `node-id`).

**Independent Test**: `POST /components` twice with the same `node-id` yields `201` then `200`; `GET /components/{node-id}` returns `200` with the stored payload.

- [x] T013 [US1] Update `POST /components` handler in `src/adapters/inbound/api/routers/components.py` to accept `ComponentNode` (`src/adapters/inbound/api/schemas/component_node.py`), call `UpsertComponentNode`, and return `201` vs `200` based on upsert result
- [x] T014 [US1] Update `GET /components/{component_id}` in `src/adapters/inbound/api/routers/components.py` to treat `component_id` as `node-id`, call `GetComponentNode`, and return the stored component-node payload using `ComponentNode` as the response model
- [x] T015 [US1] Update `src/infrastructure/main.py` and `src/adapters/inbound/api/dependencies/wiring.py` usage so the components router depends on `component_node_repository` (stop using `graph_repository` for this route)
- [x] T016 [P] [US1] Update persistence tests in `tests/test_components_persistence.py` to assert MongoDB upsert/replace semantics in the `components` collection keyed by `node-id`
- [x] T017 [P] [US1] Update endpoint tests to assert 201 on first POST, 200 on second POST, GET /components/{node-id} returns 200 with the stored payload, and GET /components/{missing-node-id} returns 404
- [x] T018 [P] [US1] Update `tests/test_components_persistence_failure.py` to assert a persistence failure during upsert returns `500 application/problem+json`

---

## Phase 4: User Story 2 — Reject Invalid Payloads (Priority: P2)

**Goal**: Reject malformed JSON with `400` and schema/constraint violations (missing required fields, unknown fields, wrong types, non-object root) with `422`.

**Independent Test**: Each invalid request scenario returns the expected status code and Problem Details response.
- [x] T019 [US2] Ensure the component-node JSON Schema enforces strictness (additionalProperties: false) at all object levels except metadata (which permits additional keys); re-run codegen only if the schema changes
- [x] T020 [P] [US2] Update invalid-payload cases in `tests/test_components_endpoint.py` for `POST /components` to cover: missing required fields, unknown top-level fields, unknown nested fields, `relationaships` typo, wrong types, and non-object JSON root → `422`
- [x] T021 [P] [US2] Update malformed JSON case in `tests/test_components_endpoint.py` for `POST /components` to assert `400 application/problem+json`

---

## Phase 5: User Story 3 — Allow Minimal Payloads (Priority: P3)

**Goal**: Allow omitting optional `interfaces` and `relationships` while still upserting successfully.

**Independent Test**: POST a payload containing only required fields succeeds with `201` (or `200` if already exists).

- [x] T022 [P] [US3] Add/update minimal-payload test in `tests/test_components_endpoint.py` to POST only required fields and assert a successful upsert response

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T023 [P] Remove or repurpose now-unused graph repository plumbing: `src/core/ports/graph_repository.py`, `src/adapters/outbound/mongodb/graph_repository.py`, and `get_graph_repository` in `src/adapters/inbound/api/dependencies/wiring.py` (only if no longer referenced)
- [x] T024 [P] Update `specs/004-components-payload-schema/quickstart.md` to include a `GET /components/{node-id}` verification step (consistent with Option C semantics)
- [x] T025 Run `pytest` to validate all updated endpoint/persistence behavior (tests under `tests/`)
- [x] T026 [P] Add an opt-in performance smoke check for SC-001: issue 100 valid requests and assert at least 95 successful responses (200/201) complete within 1 second (skipped by default; run only when explicitly enabled to avoid flaky CI)


---

## Dependencies & Execution Order

### User Story Completion Order (Dependency Graph)

- Setup (Phase 1) → Foundational (Phase 2) → US1 (Phase 3)
- US2 (Phase 4) and US3 (Phase 5) depend on US1 (they validate behaviors of the same endpoint)
- Polish (Phase 6) depends on the desired user stories being complete

### Parallel Opportunities

- Phase 1: T003 can run in parallel with T004 (different contract docs)
- Phase 2: T012 can run in parallel with T010–T011 (DI provider file is independent)
- Phase 3: T016–T018 are parallel test updates (separate test files) once routing and persistence are implemented
- Phase 4: T020 and T021 can run in parallel (same file but separate test cases; coordinate to avoid merge conflicts)

---

## Parallel Example: User Story 1

- Implement API handler changes in `src/adapters/inbound/api/routers/components.py` (T013–T015)
- In parallel, update tests in:
  - `tests/test_components_persistence.py` (T016)
  - `tests/test_components_endpoint.py` (T017)
  - `tests/test_components_persistence_failure.py` (T018)

---

## Implementation Strategy

- MVP scope: Phase 1 + Phase 2 + User Story 1 (upsert + retrieval)
- After MVP is stable, complete US2 (invalid payload coverage) and US3 (minimal payload)
- Finish with polish/cleanup (Phase 6)
