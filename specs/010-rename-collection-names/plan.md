# Implementation Plan: Rename MongoDB Collection Names

**Branch**: `010-rename-collection-names` | **Date**: 2026-05-16 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/010-rename-collection-names/spec.md`
**Input**: Feature specification from `/specs/010-rename-collection-names/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Rename the service's dashed MongoDB collection names to underscore-based equivalents while leaving
HTTP routes, Pydantic models, and core business logic unchanged. The preferred implementation is
to isolate the rename inside `src/adapters/outbound/mongodb/` by introducing a single source of
truth for collection identifiers, updating only the affected MongoDB repositories and the
Mongo-backed persistence tests that seed or verify collections by name. The feature explicitly does
not perform automatic migration of pre-existing dashed collections, so the design keeps code churn
out of the API and core layers and uses the repository's functional pytest regression gate to prove
no behavior changes beyond collection selection.

## Technical Context

**Language/Version**: Python 3.12+ (verified in the active venv on Python 3.14.3)  
**Primary Dependencies**: FastAPI, Pydantic v2, pymongo, pytest, httpx/TestClient, testcontainers[mongodb], ldap3  
**Storage**: MongoDB Atlas in production; MongoDB replica-set container for persistence-backed integration tests  
**Testing**: pytest with FastAPI `TestClient`; required functional regression command is `python -m pytest tests -v -k "not perf_smoke"`  
**Target Platform**: ASGI web service on macOS/Linux development environments and Linux server deployment targets
**Project Type**: web-service  
**Performance Goals**: No material runtime regression; collection-name lookups remain constant-time and request-path behavior remains unchanged  
**Constraints**: No automatic migration of existing dashed collections; no application-side recreation of collection indexes or validation rules; preserve document shape and transactional behavior; minimize churn outside `src/adapters/outbound/mongodb/` and the Mongo-backed persistence tests; satisfy strict clean-architecture review expectations
**Scale/Scope**: Three dashed collection identifiers in three MongoDB repository modules, plus direct collection-name assertions and seeding in two Mongo-backed persistence test modules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Required gates for this project (see `.specify/memory/constitution.md`):

- Architecture: Feature design preserves Hexagonal Architecture (Ports & Adapters).
- Core purity: `src/core/` remains framework-agnostic (no `fastapi`, `pymongo`/`motor`, `ldap3`, etc.).
- Ports: Any new external capability is introduced as an ABC in `src/core/ports/`.
- Specs-first: Any change to feature intent, behavioral requirements, or software specifications
  starts in `specs/`.
- Canonical contracts: Any change to shared or canonical data contracts starts in `schemas/`.
- Validation: Inbound adapter validates all JSON payloads via Pydantic schemas in
  `src/adapters/inbound/api/schemas/` before calling core use cases.
- Errors: New domain exceptions are defined in `src/core/exceptions/` and mapped to HTTP in
  `src/infrastructure/errors/` without leaking stack traces.
- Structure: Folder structure remains unchanged unless explicitly approved.

Gate assessment before Phase 0 research:

- Architecture: PASS. The rename is isolated to outbound MongoDB adapters and persistence-focused
  tests rather than moving persistence concerns into routers or use cases.
- Core purity: PASS. No changes are required in `src/core/`.
- Ports: PASS. No new external capability is introduced; existing repository ports remain valid.
- Specs-first: PASS. The feature specification and clarification were completed under
  `specs/010-rename-collection-names/` before design work.
- Canonical contracts: PASS. No `schemas/` update is required because JSON payload contracts do not
  change.
- Validation: PASS. Inbound validation remains unchanged because request/response models are out of
  scope.
- Errors: PASS. No new domain exceptions or HTTP mappings are introduced.
- Structure: PASS. The design reuses the existing adapter/test folders and adds only feature-spec
  artifacts under `specs/`.

## Project Structure

### Documentation (this feature)

```text
specs/010-rename-collection-names/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── collection-names.md
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
specs/
├── 010-rename-collection-names/
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   └── contracts/
│       └── collection-names.md

src/
├── adapters/
│   └── outbound/
│       └── mongodb/
│           ├── collection_names.py
│           ├── application_architecture_repository.py
│           ├── component_node_repository.py
│           ├── component_payload_repository.py
│           ├── graph_repository.py
│           ├── micro_affinity_group_repository.py
│           ├── micro_affinity_group_processed_repository.py
│           ├── transaction_manager.py
│           └── client.py
├── core/
│   ├── domain/
│   ├── ports/
│   ├── use_cases/
│   └── exceptions/
└── infrastructure/
    └── main.py

tests/
├── conftest.py
├── test_application_architectures_persistence.py
├── test_components_persistence.py
├── test_components_persistence_failure.py
├── test_component_dependencies_persistence.py
└── test_micro_affinity_groups_persistence.py
```

**Structure Decision**: Keep the rename implementation inside the existing MongoDB adapter layer by
introducing a shared collection-name mapping module under `src/adapters/outbound/mongodb/` and
updating only the repository implementations that still hardcode dashed identifiers. Restrict test
changes to persistence-backed suites and fixture consumers that directly call
`client.app.state.mongo_db.get_collection(...)`, leaving inbound routers, use cases, and pure unit
tests untouched to minimize churn for clean-architecture review. Any collection-level indexes or validators required on the underscore-based collections remain an external provisioning concern and are not created by this feature.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. The design remains within outbound MongoDB adapters and persistence tests,
  preserving thin inbound adapters and untouched core use cases.
- Core purity: PASS. No framework/driver code is introduced into `src/core/`.
- Ports: PASS. Existing repository ports remain unchanged because the rename is an adapter detail.
- Specs-first: PASS. Research, plan, data model, internal contract, and quickstart are all captured
  under `specs/010-rename-collection-names/` before implementation.
- Canonical contracts: PASS. No `schemas/` change is needed because the feature does not affect
  canonical payload contracts.
- Validation: PASS. The inbound validation layer is unaffected.
- Errors: PASS. No new domain errors or HTTP mappings are introduced.
- Structure: PASS. The design uses the baseline folder layout without architectural expansion.
