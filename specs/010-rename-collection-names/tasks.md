---

description: "Task list for implementing 010-rename-collection-names"

---

# Tasks: Rename MongoDB Collection Names

**Input**: Design documents from `specs/010-rename-collection-names/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`)

**Tests**: Automated tests are required by `spec.md` and the planning constraints. Update the Mongo-backed persistence suites and run the verified functional regression command.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently once the shared MongoDB collection-name mapping is in place.

## Phase 1: Setup (Contract Alignment)

**Purpose**: Lock the renamed collection inventory and no-migration scope before touching code.

- [X] T001 Verify `specs/010-rename-collection-names/contracts/collection-names.md`, `specs/010-rename-collection-names/research.md`, and `specs/010-rename-collection-names/quickstart.md` still match the clarified no-migration scope, the dashed collection inventory, and the external provisioning assumption for indexes and validators

- [X] T002 [P] Create shared MongoDB collection name constants in `src/adapters/outbound/mongodb/collection_names.py` for renamed and unchanged collections

---

## Phase 2: Foundational (Blocking Adapter Boundary)

**Purpose**: Establish the low-churn implementation boundary that all stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Keep the collection rename isolated to `src/adapters/outbound/mongodb/` by leaving `src/infrastructure/main.py`, `src/core/ports/application_architecture_repository.py`, `src/core/ports/micro_affinity_group_repository.py`, and `src/core/ports/micro_affinity_group_processed_repository.py` functionally unchanged while the existing startup wiring continues to construct the same repository classes

**Checkpoint**: A shared collection-name mapping exists and the rename boundary is confined to outbound MongoDB adapters plus persistence-focused tests.

---

## Phase 3: User Story 1 - Use Renamed Application Architecture Collections Transparently (Priority: P1) 🎯 MVP

**Goal**: Make application architecture persistence use `application_architectures` without changing API or repository behavior.

**Independent Test**: Run `tests/test_application_architectures_persistence.py` and verify reads, upserts, and version coexistence still pass while MongoDB assertions target `application_architectures`.

### Tests for User Story 1

- [X] T004 [P] [US1] Update `tests/test_application_architectures_persistence.py` so direct MongoDB assertions use `application_architectures` through `src/adapters/outbound/mongodb/collection_names.py`

### Implementation for User Story 1

- [X] T005 [US1] Update `src/adapters/outbound/mongodb/application_architecture_repository.py` to read and write `application_architectures` through `src/adapters/outbound/mongodb/collection_names.py`

**Checkpoint**: Application architecture persistence works against the underscore-based collection with unchanged functional behavior.

---

## Phase 4: User Story 2 - Keep Micro Affinity Group Persistence and Test Seeding Consistent (Priority: P2)

**Goal**: Keep raw and processed micro affinity group persistence, architecture seeding, and direct MongoDB assertions aligned on the underscore-based collection names.

**Independent Test**: Run `tests/test_micro_affinity_groups_persistence.py` and verify raw writes, processed writes, rollback checks, and architecture seeding all succeed using `application_architectures`, `micro_affinity_groups`, and `micro_affinity_groups_processed`.

### Tests for User Story 2

- [X] T006 [P] [US2] Update `tests/test_micro_affinity_groups_persistence.py` so architecture seeding and raw/processed collection assertions use `application_architectures`, `micro_affinity_groups`, and `micro_affinity_groups_processed`

### Implementation for User Story 2

- [X] T007 [US2] Update `src/adapters/outbound/mongodb/micro_affinity_group_repository.py` and `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py` to use the shared underscore-based collection names from `src/adapters/outbound/mongodb/collection_names.py`
- [X] T008 [US2] Verify `src/adapters/outbound/mongodb/transaction_manager.py`, `src/adapters/outbound/mongodb/micro_affinity_group_repository.py`, and `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py` preserve the existing raw-plus-processed transactional behavior with only collection identifiers changed

**Checkpoint**: The micro affinity group persistence flow and its MongoDB-backed tests are fully aligned on the renamed collections.

---
## Phase 5: User Story 3 - Preserve Behavior and Avoid Regressions During the Rename (Priority: P3)

**Goal**: Prove the rename changes only collection identifiers, preserves unchanged collections, and does not regress functional behavior.

**Independent Test**: Verify the targeted MongoDB adapters and persistence tests contain no dashed collection identifiers for renamed collections, then run the full functional regression suite and confirm it remains green.

### Tests for User Story 3

- [X] T009 [P] [US3] Update `specs/010-rename-collection-names/quickstart.md` with the final search and pytest verification steps for underscore-based collection names, the no-migration assumption, and the external provisioning note for any required indexes or validators

- [X] T010 [P] [US3] Update `specs/010-rename-collection-names/contracts/collection-names.md` with the final implementation-time mapping, unchanged-collection inventory, and the out-of-scope note for index and validator recreation if delivery details shift

### Implementation for User Story 3

- [X] T011 [US3] Run `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v -k "not perf_smoke"` and verify `src/adapters/outbound/mongodb/application_architecture_repository.py`, `src/adapters/outbound/mongodb/micro_affinity_group_repository.py`, `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py`, `tests/test_application_architectures_persistence.py`, and `tests/test_micro_affinity_groups_persistence.py` no longer reference dashed collection names for renamed collections

**Checkpoint**: The renamed collection contract, documentation, and functional regression behavior all match the specification.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish optional validation and repository metadata updates that span the stories.

- [X] T012 [P] Re-run `.specify/scripts/bash/update-agent-context.sh copilot` if implementation changes the technical context recorded in `specs/010-rename-collection-names/plan.md`
- [X] T013 [P] Run `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v` for broader confirmation if reviewer expectations or CI parity require the optional full-suite check after T011

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately and locks the renamed collection inventory before implementation.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion and delivers the MVP rename for application architecture persistence.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because micro affinity group persistence also relies on the renamed application architecture collection during Mongo-backed verification.
- **User Story 3 (Phase 5)**: Depends on User Story 1 and User Story 2 because it validates the final renamed collection contract and regression behavior.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 and has no dependency on other user stories.
- **US2 (P2)**: Depends on US1 because the micro affinity group persistence flow seeds and reads the renamed application architecture collection.
- **US3 (P3)**: Depends on US1 and US2 because it verifies the final implementation state and the full functional regression gate.

### Within Each User Story

- Update the Mongo-backed persistence tests before finalizing the repository changes they validate.
- Keep the rename inside `src/adapters/outbound/mongodb/` and Mongo-backed persistence tests; do not expand changes into routers, schemas, or core use cases.
- Validate the no-migration assumption and renamed collection inventory after repository/test alignment is complete.
- Run the functional regression gate after all renamed collection references are updated.

### Parallel Opportunities

- Phase 1: T001 and T002 can run in parallel because they touch specification artifacts and a new persistence-layer constants module separately.
- Phase 5: T009 and T010 can run in parallel because they update different feature-spec artifacts.
- Phase 6: T012 and T013 can run in parallel because agent-context refresh and optional full-suite confirmation are independent cross-cutting follow-ups.

---

## Parallel Example: User Story 2

```bash
# Align the micro affinity group persistence surface together:
Task: "Update tests/test_micro_affinity_groups_persistence.py so architecture seeding and raw/processed collection assertions use underscore-based collection names"
Task: "Update src/adapters/outbound/mongodb/micro_affinity_group_repository.py and src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py to use shared underscore-based collection names"
```

---

## Parallel Example: User Story 3

```bash
# Final contract verification tasks can proceed together:
Task: "Update specs/010-rename-collection-names/quickstart.md with final verification steps"
Task: "Update specs/010-rename-collection-names/contracts/collection-names.md with the final implementation-time mapping"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate `tests/test_application_architectures_persistence.py` independently before expanding the rename to the micro affinity group flow

### Incremental Delivery

1. Deliver US1 to prove the underscore rename works for the application architecture repository
2. Deliver US2 to align the raw and processed micro affinity group collections and their test seeding
3. Deliver US3 to lock down no-regression behavior and the clarified no-migration contract
4. Finish with optional broader validation and agent-context refresh if needed

### Parallel Team Strategy

1. One developer can prepare `src/adapters/outbound/mongodb/collection_names.py` while another verifies the no-migration contract artifacts in Phase 1
2. After Phase 2, a developer can update the persistence tests while another updates the targeted repository files within the same user story
3. Once repository and test alignment is complete, regression/documentation work can proceed in parallel during US3 and Polish

---

## Notes

- [P] tasks touch different files and do not depend on unfinished tasks in the same phase.
- The required regression gate for this feature is the verified functional command `python -m pytest tests -v -k "not perf_smoke"`.
- Keep collection-name changes inside the outbound MongoDB adapter layer and the Mongo-backed persistence tests to satisfy the review-readiness constraint.
- Existing dashed collections are not migrated automatically; implementation should not add runtime dual-write or migration logic.