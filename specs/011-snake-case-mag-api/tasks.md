---

description: "Task list for implementing 011-snake-case-mag-api"

---

# Tasks: Snake Case MAG API

**Input**: Design documents from `specs/011-snake-case-mag-api/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Tests**: Automated tests are required by `spec.md` and by the user request. Update the MAG-focused pytest suites first, then run the required functional regression command.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently once the shared contract and generated-model baseline is updated.

## Phase 1: Setup (Contract Source Alignment)

**Purpose**: Lock the snake_case request and response contract inputs before touching runtime code.

- [X] T001 [P] Update `specs/samples/micro-affinity-group/micro-affinity-group.json` and `specs/samples/micro-affinity-group/micro-affinity-group-relationships.json` so every MAG request/response key uses `snake_case`
- [X] T002 [P] Update the service-local MAG contract source schemas in `specs/001-service-skeleton/contracts/micro_affinity_group.schema.json` and `specs/001-service-skeleton/contracts/micro_affinity_group_processed.schema.json` so the generated MAG JSON Schemas use `snake_case` property names only

---

## Phase 2: Foundational (Blocking Codegen and Route Boundary)

**Purpose**: Regenerate the shared MAG adapter models and preserve the existing route boundary before any user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Run `generate_inbound_models.sh` and update the request and response Pydantic contract models in `src/adapters/inbound/api/schemas/micro_affinity_group.py` and `src/adapters/inbound/api/schemas/micro_affinity_group_processed.py` so the regenerated MAG models keep the custom `MicroAffinityGroup` wrapper while removing MAG kebab-case aliases
- [X] T004 Verify and preserve the existing `/v1/micro-affinity-groups` route and DI surface in `src/adapters/inbound/api/routers/micro_affinity_groups.py`, `src/infrastructure/main.py`, and `tests/conftest.py` while the MAG contract changes to snake_case only

**Checkpoint**: The authoritative MAG samples, JSON Schemas, and generated inbound models all describe the same snake_case contract, and the existing route path remains unchanged.

---

## Phase 3: User Story 1 - Submit Snake Case Requests (Priority: P1) 🎯 MVP

**Goal**: Accept snake_case MAG submissions and reject legacy kebab-case request bodies without changing route behavior.

**Independent Test**: Submit a valid snake_case body to `/v1/micro-affinity-groups` and confirm it succeeds, then submit the equivalent kebab-case body and confirm validation rejects it.

### Tests for User Story 1

- [X] T005 [P] [US1] Update request-validation and request-success coverage in `tests/test_micro_affinity_groups_endpoint.py` so `/v1/micro-affinity-groups` accepts snake_case payloads and rejects legacy kebab-case MAG keys
- [X] T006 [P] [US1] Update request-side MAG fixtures in `tests/test_micro_affinity_group_use_case.py` and `tests/test_micro_affinity_group_relationship_mapper.py` so submitted MAG payloads use `micro_ag_id`, `parent_asset_id`, `architecture_version`, `effective_date`, and `asset_id`

### Implementation for User Story 1

- [X] T007 [US1] Update `src/adapters/inbound/api/routers/micro_affinity_groups.py` so `payload.model_dump(...)` passes native snake_case MAG data into the use case without alias translation
- [X] T008 [US1] Update `src/core/use_cases/upsert_micro_affinity_group.py` so MAG identity and lookup fields are read from `micro_ag_id`, `parent_asset_id`, `architecture_version`, and `effective_date`
- [X] T009 [US1] Update `src/core/domain/micro_affinity_group_relationship_mapper.py` so submitted MAG workloads are consumed from snake_case request keys while existing application architecture lookup rules and domain errors remain unchanged

**Checkpoint**: Snake_case MAG requests work end-to-end through the router and use case, and legacy kebab-case request keys no longer pass validation.

---

## Phase 4: User Story 2 - Receive Snake Case Responses (Priority: P2)

**Goal**: Return enriched MAG responses using snake_case keys only, including nested relationship objects.

**Independent Test**: Post a valid snake_case request and confirm the success response contains only `snake_case` keys, including `source_workload`, `destination_workload`, and nested `asset_id` fields.

### Tests for User Story 2

- [X] T010 [P] [US2] Update response assertions in `tests/test_micro_affinity_groups_endpoint.py` and request/response builders in `tests/test_perf_smoke_micro_affinity_groups.py` so successful MAG responses use snake_case keys only
- [X] T011 [P] [US2] Update processed-payload expectations in `tests/test_micro_affinity_group_use_case.py` and `tests/test_micro_affinity_group_relationship_mapper.py` so generated relationships use `source_workload`, `destination_workload`, and nested `asset_id`

### Implementation for User Story 2

- [X] T012 [US2] Update `src/core/domain/micro_affinity_group_relationship_mapper.py` so generated processed MAG payloads emit `source_workload`, `destination_workload`, and nested `asset_id` keys while preserving existing enrichment behavior
- [X] T013 [US2] Validate the regenerated response Pydantic contract model flow in `src/adapters/inbound/api/schemas/micro_affinity_group_processed.py` and `src/adapters/inbound/api/routers/micro_affinity_groups.py` so successful endpoint responses serialize snake_case fields only

**Checkpoint**: The endpoint returns only snake_case response payloads and the enriched relationship structure stays behaviorally unchanged.

---

## Phase 5: User Story 3 - Persist Snake Case Documents (Priority: P3)

**Goal**: Persist newly written raw and processed MAG MongoDB documents using snake_case identity and payload keys only.

**Independent Test**: Post a valid snake_case MAG request and verify raw and processed MongoDB records are queried and asserted by snake_case identity fields and stored with snake_case keys only.

### Tests for User Story 3

- [X] T014 [P] [US3] Update `tests/test_micro_affinity_groups_persistence.py` so MAG persistence seeding, MongoDB query filters, and stored-document assertions use `micro_ag_id`, `architecture_version`, `effective_date`, `asset_id`, `source_workload`, and `destination_workload`

### Implementation for User Story 3

- [X] T015 [US3] Update `src/adapters/outbound/mongodb/micro_affinity_group_repository.py` and `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py` so new MAG records are queried and upserted with snake_case identity and payload keys only
- [X] T016 [US3] Verify `src/core/use_cases/upsert_micro_affinity_group.py` and `src/adapters/outbound/mongodb/transaction_manager.py` preserve the existing raw-plus-processed transactional behavior while historical kebab-case documents remain out of migration scope

**Checkpoint**: Newly written MAG persistence output is fully aligned with the snake_case API contract and transactional behavior is unchanged.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish verification, architecture checks, and final documentation alignment across the completed stories.

- [X] T017 [P] Update `specs/011-snake-case-mag-api/contracts/http-api.md` and `specs/011-snake-case-mag-api/quickstart.md` with any final implementation-time verification details discovered while completing the MAG migration
- [X] T018 Run `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python check_core_purity.py` to confirm `src/core/` remains free of forbidden framework and driver imports after the MAG snake_case migration
- [X] T019 Run `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests/test_micro_affinity_group_relationship_mapper.py tests/test_micro_affinity_group_use_case.py tests/test_micro_affinity_groups_endpoint.py tests/test_micro_affinity_groups_persistence.py -v` to validate the focused MAG regression surface
- [X] T020 Run `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v -k "not perf_smoke"` and record the final result in `specs/011-snake-case-mag-api/quickstart.md`
- [X] T021 [P] If `tests/test_perf_smoke_micro_affinity_groups.py` is updated, run `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests/test_perf_smoke_micro_affinity_groups.py -v` to verify the snake_case perf-smoke fixture and response-builder surface

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and locks the snake_case contract sources before any runtime edits.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories until regenerated MAG models and route invariants are in place.
- **User Story 1 (Phase 3)**: Depends on Foundational completion and delivers the MVP snake_case request path.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because snake_case response serialization builds on the accepted snake_case request path and the same MAG mapper/router surface.
- **User Story 3 (Phase 5)**: Depends on User Story 1 and User Story 2 because persistence must align with the final accepted request and returned response shape.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 and has no dependency on other user stories.
- **US2 (P2)**: Depends on US1 because the processed response shape is produced from the snake_case request path.
- **US3 (P3)**: Depends on US1 and US2 because the persisted raw and processed shapes must match the final snake_case request/response contract.

### Within Each User Story

- Update the relevant pytest fixtures and assertions before finalizing the implementation they validate.
- Keep the MAG migration inside the existing contract files, generated inbound schemas, router, use case, mapper, MongoDB repositories, and MAG-focused tests.
- Preserve the existing `/v1/micro-affinity-groups` route path, error semantics, and transactional write behavior while changing only MAG field naming.
- Run the focused MAG regression before the full functional regression gate.

### Parallel Opportunities

- Phase 1: T001 and T002 can run in parallel because the sample documents and JSON Schema files are separate contract sources.
- Phase 3: T005 and T006 can run in parallel because they update different MAG test modules.
- Phase 4: T010 and T011 can run in parallel because they update different response-oriented test surfaces.
- Phase 6: T017 and T018 can run in parallel because final doc alignment and core-purity verification do not modify the same files.
- Phase 6: T021 can run independently after the implementation updates if the perf-smoke MAG test file changed.

---

## Parallel Example: User Story 1

```bash
# Update the request-facing MAG tests together:
Task: "Update tests/test_micro_affinity_groups_endpoint.py so /v1/micro-affinity-groups accepts snake_case payloads and rejects legacy kebab-case MAG keys"
Task: "Update tests/test_micro_affinity_group_use_case.py and tests/test_micro_affinity_group_relationship_mapper.py so submitted MAG payload fixtures use snake_case fields"
```

---

## Parallel Example: User Story 2

```bash
# Align response-oriented MAG assertions together:
Task: "Update tests/test_micro_affinity_groups_endpoint.py and tests/test_perf_smoke_micro_affinity_groups.py so successful MAG responses use snake_case keys only"
Task: "Update tests/test_micro_affinity_group_use_case.py and tests/test_micro_affinity_group_relationship_mapper.py so generated relationships use source_workload, destination_workload, and nested asset_id"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate that `/v1/micro-affinity-groups` accepts snake_case requests and rejects kebab-case requests before expanding into response and persistence work.

### Incremental Delivery

1. Deliver the contract-source and generated-model baseline in Phases 1 and 2.
2. Deliver US1 to make snake_case requests work end-to-end.
3. Deliver US2 to make success responses snake_case-only.
4. Deliver US3 to align MongoDB persistence with the final contract.
5. Finish with purity checks, focused MAG regression, and the full functional regression gate.

### Parallel Team Strategy

1. One developer can update the MAG sample documents while another updates the MAG JSON Schemas in Phase 1.
2. After Phase 2, one developer can update endpoint request tests while another updates use-case and mapper request fixtures for US1.
3. During US2, one developer can handle endpoint/perf-smoke response assertions while another updates mapper/use-case processed-payload expectations.

---

## Notes

- [P] tasks touch different files and do not depend on unfinished tasks in the same phase.
- The required regression gate for this feature is `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v -k "not perf_smoke"`.
- The MAG perf-smoke test is optional verification only and is not part of the required non-perf functional regression gate.
- The route path remains `/v1/micro-affinity-groups`; only MAG request, response, generated-model, and new persistence key naming changes.
- Historical kebab-case MongoDB documents remain out of scope for migration, dual-write, or compatibility query logic.