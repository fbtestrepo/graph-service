---

description: "Task list for implementing 005-component-dependencies"

---

# Tasks: Component Dependencies Graph

**Input**: Design documents from `specs/005-component-dependencies/` (plan.md, spec.md, data-model.md, research.md, contracts/, quickstart.md)

**Authoritative contracts**: `specs/001-service-skeleton/contracts/` (used by `generate_inbound_models.sh`)

## Phase 1: Setup (Specs-first Contracts + Codegen)

**Purpose**: Make contracts authoritative and generate inbound Pydantic models.

- [x] T001 Add JSON Schema `specs/001-service-skeleton/contracts/dependency_edge.schema.json` (copy from `specs/005-component-dependencies/contracts/dependency_edge.schema.json`)
- [x] T002 Add JSON Schema `specs/001-service-skeleton/contracts/component_dependencies_response.schema.json` (copy from `specs/005-component-dependencies/contracts/component_dependencies_response.schema.json`)
- [x] T003 Update OpenAPI `specs/001-service-skeleton/contracts/openapi.yaml` to add `GET /components/{node_id}/dependencies` with `200` response `component_dependencies_response.schema.json` and `404/500` Problem Details
- [x] T004 [P] Update `specs/001-service-skeleton/contracts/http-api.md` to document `GET /components/{node_id}/dependencies` semantics (two directed traversals from root, 20-hop cap with boundary rule, self-sourced relationship filter, deterministic ordering)
- [x] T005 [P] Sync working-copy contracts in `specs/005-component-dependencies/contracts/openapi.yaml` and `specs/005-component-dependencies/contracts/http-api.md` with the authoritative definitions (ensure path, responses, and schema refs match)
- [x] T006 Update codegen script `generate_inbound_models.sh` to generate `src/adapters/inbound/api/schemas/component_dependencies_response.py` from `specs/001-service-skeleton/contracts/component_dependencies_response.schema.json`
- [x] T007 Run `./generate_inbound_models.sh` and verify `src/adapters/inbound/api/schemas/component_dependencies_response.py` has correct field aliases (`node-id`, `dependency-graph`) and forbids unknown fields (`extra='forbid'`)

---

## Phase 2: Foundational (Ports, Use Case, Outbound Adapter)

**Purpose**: Add core traversal logic and repository support for upstream + downstream edge discovery.

- [x] T008 [P] Add core domain type `src/core/domain/dependency_edge.py` representing an edge `(relationship_type, source_node_id, target_node_id)` and a stable dedup/sort key
- [x] T009 Extend core port `src/core/ports/component_node_repository.py` with `get_outgoing_relationship_edges(source_node_ids: set[str]) -> list[DependencyEdge]` and `get_incoming_relationship_edges(target_node_ids: set[str]) -> list[DependencyEdge]` (both must return only “self-sourced” relationships where `relationship.source.node-id == document.node-id`)
- [x] T010 Implement the new port methods in `src/adapters/outbound/mongodb/component_node_repository.py` using efficient MongoDB queries (outgoing by `node-id ∈ source_node_ids`, incoming by `relationships.target.node-id ∈ target_node_ids`) and in-Python filtering for “self-sourced” relationships
- [x] T011 Implement core use case `src/core/use_cases/get_component_dependencies.py` to compute transitive upstream+downstream edges via two directed, level-order traversals with a 20-hop cap and boundary rule, include cycle-closing edges without infinite expansion, deduplicate+sort deterministically, and raise `src/core/exceptions/component_not_found.py` when the root node-id is missing

---

## Phase 3: User Story 1 — Retrieve Dependencies (Priority: P1) 🎯 MVP

**Goal**: Return the full transitive dependency graph (upstream + downstream) for a root node-id as a stable, deduplicated edge list.

**Independent Test**: Seed a small chain around `mAG_A` and call `GET /components/mAG_A/dependencies`; verify the returned `dependency-graph` contains direct + indirect edges (and upstream edges that reference `mAG_A`).


- [x] T012 [US1] Add endpoint `GET /components/{node_id}/dependencies` in `src/adapters/inbound/api/routers/components.py` using `ComponentDependenciesResponse` (`src/adapters/inbound/api/schemas/component_dependencies_response.py`) and `GetComponentDependencies` (`src/core/use_cases/get_component_dependencies.py`)
- [x] T013 [P] [US1] Add endpoint unit tests in `tests/test_component_dependencies_endpoint.py` using a fake `ComponentNodeRepository` to assert the response shape matches `specs/sample-component-dependencies/sample-mag-dependencies.json` for a seeded chain
- [x] T014 [P] [US1] Add Mongo integration test in `tests/test_component_dependencies_persistence.py` that persists a small multi-hop graph into the `components` collection and asserts upstream + downstream traversal returns the expected transitive edge list. includes FR-011: edge to a non-existent node-id is still returned; no expansion beyond it

---

## Phase 4: User Story 2 — Missing Root Node Returns Not Found (Priority: P2)

**Goal**: Distinguish “unknown component” from “known component with no dependencies” by returning 404 when the root node-id does not exist.

**Independent Test**: `GET /components/does-not-exist/dependencies` returns `404 application/problem+json`.


- [x] T015 [P] [US2] Add a `GET /components/{node_id}/dependencies` missing-root test case in `tests/test_component_dependencies_endpoint.py` asserting `404 application/problem+json` with `error_code == "component_not_found"`

---

## Phase 5: User Story 3 — Stable, Deduplicated Edge Lists (Priority: P3)

**Goal**: Ensure each unique edge appears once and the edge list ordering is deterministic.

**Independent Test**: Seed duplicated/cyclic edges and verify the response is deduplicated and sorted by `(relationship-type, source-node-id, target-node-id)`.

- [x] T016 [P] [US3] Add core unit tests in `tests/test_component_dependencies_use_case.py` to validate: deduplication, deterministic sorting, inclusion of cycle-closing edges without infinite loops, FR-011 (missing-node edge inclusion), and FR-014 (ignore relationships where relationship.source.node-id != document.node-id)
- [x] T017 [P] [US3] Add a depth-cap boundary unit test in `tests/test_component_dependencies_use_case.py` covering the FR-013 boundary rule (do not introduce hop-21 nodes; allow in-scope depth-20 incident edges only when both endpoints are already within ≤ 20 hops from the root)

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T018 [P] Update `specs/005-component-dependencies/quickstart.md` if needed so it matches the implemented endpoint behavior and produces the expected edges
- [x] T019 [P] Add opt-in performance smoke test `tests/test_perf_smoke_dependencies.py` (skipped by default via env var) that issues 100 HTTP requests to GET /components/{node_id}/dependencies against a fake repository preloaded with ≥100 edges and asserts at least 95 complete within 1s (align with SC-003 intent)
- [x] T020 Run `pytest` to validate the full suite (unit + integration under `tests/`)

---

## Dependencies & Execution Order

### User Story Completion Order (Dependency Graph)

- Setup (Phase 1) → Foundational (Phase 2) → US1 (Phase 3)
- US2 (Phase 4) and US3 (Phase 5) depend on US1 (they validate behaviors of the same endpoint)
- Polish (Phase 6) depends on the desired user stories being complete

### Parallel Opportunities

- Phase 1: T004 and T005 can run in parallel (different docs)
- Phase 2: T008 can run in parallel with T009 (domain type vs port definition), but both must complete before T011
- Phase 3: T013 and T014 are parallel tests once T012 exists (separate files)
- Phase 5: T016 and T017 are parallel test additions (same file; coordinate to avoid merge conflicts)

---

## Parallel Examples

### User Story 1

- Implement the endpoint handler in `src/adapters/inbound/api/routers/components.py` (T012)
- In parallel (after T012), add tests in `tests/test_component_dependencies_endpoint.py` (T013) and `tests/test_component_dependencies_persistence.py` (T014)

### User Story 2

- Add the missing-root 404 test case in `tests/test_component_dependencies_endpoint.py` (T015) while another developer works on US3 tests

### User Story 3

- Add sorting/dedup/cycle unit tests (T016) and the depth-cap boundary unit test (T017) together in `tests/test_component_dependencies_use_case.py` (coordinate to avoid merge conflicts)

---

## Implementation Strategy

- MVP scope: Phase 1 + Phase 2 + User Story 1 (end-to-end dependencies endpoint)
- After MVP is stable, add US2 (404 behavior) and US3 (ordering/dedup + depth boundary)
- Finish with polish/perf smoke + `pytest`
