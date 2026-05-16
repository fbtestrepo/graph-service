---

description: "Task list for implementing 009-v1-api-prefixing"

---

# Tasks: V1 API Version Prefixing

**Input**: Design documents from `specs/009-v1-api-prefixing/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Tests**: Automated tests are required by `spec.md` and the planning constraints. Update the affected pytest/TestClient suites and run the verified functional regression command.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently once the shared FastAPI route registration work is complete.

## Phase 1: Setup (Route Contract Alignment)

**Purpose**: Finalize the route inventory and shared test references before code changes begin.

- [X] T001 Verify `specs/009-v1-api-prefixing/contracts/http-api.md`, `specs/009-v1-api-prefixing/contracts/openapi.yaml`, and `specs/009-v1-api-prefixing/quickstart.md` still match the implemented `/v1` business route catalog and root infrastructure exclusions

- [X] T002 Add shared route-path helpers or constants for `/v1` business routes and root infrastructure routes in `tests/conftest.py`

---

## Phase 2: Foundational (Blocking FastAPI Route Assembly)

**Purpose**: Introduce the single FastAPI version boundary that every user story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Implement a versioned FastAPI router assembly in `src/infrastructure/main.py` that mounts the existing business routers under `/v1` using native router composition instead of rewriting each router module
- [X] T004 Keep `src/adapters/inbound/api/routers/components.py`, `src/adapters/inbound/api/routers/component_validation.py`, `src/adapters/inbound/api/routers/application_architectures.py`, and `src/adapters/inbound/api/routers/micro_affinity_groups.py` functionally unchanged while registering them only through the versioned boundary in `src/infrastructure/main.py`

**Checkpoint**: The app bootstrap publishes only the supported `/v1` business surface while preserving the existing router internals.

---

## Phase 3: User Story 1 - Call Versioned Business Routes (Priority: P1) 🎯 MVP

**Goal**: Make every in-scope business endpoint reachable at `/v1/...` without changing handler semantics.

**Independent Test**: Run the endpoint and persistence suites for components, application architectures, and micro affinity groups using `/v1` paths and verify the same status codes and response contracts still pass.

### Tests for User Story 1

- [X] T005 [P] [US1] Update `tests/test_validation_endpoint.py` and `tests/test_components_endpoint.py` so component validation and component endpoint requests target `/v1/components/validate`, `/v1/components`, and `/v1/components/{component_id}`
- [X] T006 [P] [US1] Update `tests/test_component_dependencies_endpoint.py`, `tests/test_components_persistence.py`, `tests/test_components_persistence_failure.py`, and `tests/test_component_dependencies_persistence.py` so dependency and component persistence requests target `/v1/components/{node_id}/dependencies` and `/v1/components`
- [X] T007 [P] [US1] Update `tests/test_application_architectures_endpoint.py`, `tests/test_application_architectures_persistence.py`, `tests/test_micro_affinity_groups_endpoint.py`, and `tests/test_micro_affinity_groups_persistence.py` so application architecture and micro affinity group requests target `/v1/application-architectures` and `/v1/micro-affinity-groups`

### Implementation for User Story 1

- [X] T008 [US1] Finalize `src/infrastructure/main.py` so the composed `/v1` router publishes component validation, components, component dependencies, application architectures, and micro affinity groups with unchanged handler wiring and status behavior

**Checkpoint**: All in-scope business routes work through `/v1` and preserve their current endpoint semantics.

---

## Phase 4: User Story 2 - Preserve Root Infrastructure Access (Priority: P2)

**Goal**: Keep health and automatic documentation available at the root path after business routes move under `/v1`.

**Independent Test**: Request `/health`, `/docs`, `/redoc`, and `/openapi.json` against the migrated app and verify they remain available from the root path.

### Tests for User Story 2

- [X] T009 [US2] Add root infrastructure route coverage in `tests/test_infrastructure_routes.py` for `GET /health`, `GET /docs`, `GET /redoc`, and `GET /openapi.json`

### Implementation for User Story 2

- [X] T010 [US2] Refine `src/infrastructure/main.py` so `health_router` remains mounted at root and FastAPI-generated `/docs`, `/redoc`, and `/openapi.json` stay unversioned after the business router composition is introduced

**Checkpoint**: Operational and documentation endpoints remain reachable at root while business endpoints stay under `/v1`.

---

## Phase 5: User Story 3 - Avoid Behavioral Regressions During Path Change (Priority: P3)

**Goal**: Ensure the route migration removes the old supported business paths, keeps OpenAPI aligned with `/v1`, and leaves endpoint behavior unchanged.

**Independent Test**: Verify the root OpenAPI document lists only the `/v1` business paths, former root business paths are no longer supported, and the functional regression suite remains green.

### Tests for User Story 3
- [X] T011 [P] [US3] Add legacy-root rejection checks to `tests/test_validation_endpoint.py`, `tests/test_components_endpoint.py`, `tests/test_component_dependencies_endpoint.py`, `tests/test_application_architectures_endpoint.py`, and `tests/test_micro_affinity_groups_endpoint.py` for the former root business paths, including `/components/{node_id}/dependencies`

- [X] T012 [P] [US3] Extend `tests/test_infrastructure_routes.py` to assert that `/openapi.json` advertises `/v1/components`, `/v1/application-architectures`, and `/v1/micro-affinity-groups` and does not publish the former root business paths as supported routes

### Implementation for User Story 3

- [X] T013 [US3] Remove any lingering root business router registrations in `src/infrastructure/main.py` so the root contract exposes only infrastructure routes while preserving existing business-handler behavior behind `/v1`

**Checkpoint**: The published contract, supported paths, and runtime behavior all match the specification.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Align optional route callers, documentation, and the final regression gate across all stories.

- [X] T014 [P] Update `tests/test_perf_smoke_components.py`, `tests/test_perf_smoke_dependencies.py`, and `tests/test_perf_smoke_micro_affinity_groups.py` so optional perf-smoke requests use the `/v1` business paths
- [X] T015 [P] Update `README.md` and `specs/009-v1-api-prefixing/quickstart.md` with the final `/v1` business route examples and root infrastructure route verification steps
- [X] T016 Run `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v -k "not perf_smoke"` and validate the manual verification flow documented in `specs/009-v1-api-prefixing/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and aligns route references before implementation.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion and delivers the MVP `/v1` business route surface.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and verifies root infrastructure route preservation.
- **User Story 3 (Phase 5)**: Depends on User Story 1 and User Story 2 because it validates the final published contract after both the `/v1` migration and root-route preservation are in place.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 and has no dependency on other user stories.
- **US2 (P2)**: Starts after Phase 2 and has no dependency on other user stories.
- **US3 (P3)**: Depends on US1 and US2 because it validates the final contract surface and regression behavior.

### Within Each User Story

- Update the relevant pytest suites before finalizing the bootstrap changes.
- Keep the existing router modules unchanged where possible; apply versioning in the app assembly layer.
- Validate OpenAPI and legacy-route behavior only after the `/v1` surface and root infrastructure routes are both in place.
- Run the functional regression gate after all route-path updates are complete.

### Parallel Opportunities

- Phase 1: T001 and T002 can run in parallel because they touch documentation and test scaffolding separately.
- Phase 3: T005, T006, and T007 can run in parallel because they target disjoint endpoint and persistence test groups.
- Phase 5: T011 and T012 can run in parallel because they target separate regression concerns in different test files.
- Phase 6: T014 and T015 can run in parallel because they update optional perf smoke tests and documentation separately.

---

## Parallel Example: User Story 1

```bash
# Update the /v1 test coverage tracks together:
Task: "Update tests/test_validation_endpoint.py and tests/test_components_endpoint.py so component requests target /v1"
Task: "Update tests/test_component_dependencies_endpoint.py, tests/test_components_persistence.py, tests/test_components_persistence_failure.py, and tests/test_component_dependencies_persistence.py so dependency/component persistence requests target /v1"
Task: "Update tests/test_application_architectures_endpoint.py, tests/test_application_architectures_persistence.py, tests/test_micro_affinity_groups_endpoint.py, and tests/test_micro_affinity_groups_persistence.py so application architecture and micro affinity group requests target /v1"
```

---

## Parallel Example: User Story 3

```bash
# Validate the final contract surface in parallel:
Task: "Add legacy-root rejection checks to the endpoint suites for former root business paths"
Task: "Extend tests/test_infrastructure_routes.py to assert the root OpenAPI document publishes only /v1 business paths"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate `/v1` business routes through the updated endpoint and persistence tests

### Incremental Delivery

1. Deliver US1 to move the business surface to `/v1`
2. Deliver US2 to prove infrastructure routes remain stable at root
3. Deliver US3 to lock down the final public contract and legacy-path behavior
4. Finish with documentation, optional perf-smoke alignment, and the verified functional regression run

### Parallel Team Strategy

1. One developer can handle `src/infrastructure/main.py` while another prepares the route-path helpers in `tests/conftest.py`
2. After Phase 2, the endpoint and persistence test-file groups in US1 can be updated in parallel
3. Once US1 and US2 are stable, regression and documentation work can proceed in parallel during Polish

---

## Notes

- [P] tasks touch different files and do not depend on unfinished tasks in the same phase.
- `tests/test_infrastructure_routes.py` is introduced to capture the root-route guarantees missing from the current suite.
- The required regression gate for this feature is the verified functional command `python -m pytest tests -v -k "not perf_smoke"`.
- Keep FastAPI versioning in the bootstrap layer rather than embedding `/v1` into each business router module.