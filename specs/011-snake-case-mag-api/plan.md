# Implementation Plan: Snake Case MAG API

**Branch**: `011-snake-case-mag-api` | **Date**: 2026-05-16 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/011-snake-case-mag-api/spec.md`
**Input**: Feature specification from `/specs/011-snake-case-mag-api/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Update the `/v1/micro-affinity-groups` contract so new requests, responses, generated Pydantic
models, and newly persisted raw and processed MongoDB documents use native `snake_case` keys.
The design starts at the authoritative MAG sample documents and JSON Schema contracts under
`specs/`, regenerates the inbound adapter models, removes alias-based kebab-case translation at
the FastAPI boundary, updates the MAG-specific core and MongoDB adapter key access to
`snake_case`, and synchronizes endpoint, use-case, mapper, persistence, and functional regression
tests. For this feature, the concrete request and response contract models are the regenerated MAG
schema modules in `src/adapters/inbound/api/schemas/`. Historical kebab-case MongoDB documents
remain untouched and no dual-format compatibility layer is added.

## Technical Context

**Language/Version**: Python 3.12+ (active workspace venv previously verified on Python 3.14.3)  
**Primary Dependencies**: FastAPI, Pydantic v2, datamodel-code-generator, pymongo, pytest, httpx/TestClient, testcontainers[mongodb], ldap3  
**Storage**: MongoDB Atlas in production; MongoDB replica-set container for persistence-backed integration tests  
**Testing**: pytest with FastAPI `TestClient`; required functional regression command is `python -m pytest tests -v -k "not perf_smoke"`  
**Target Platform**: ASGI web service for macOS/Linux development and Linux server deployment targets
**Project Type**: web-service  
**Performance Goals**: No separate performance requirement for this feature. The change is limited to contract naming, generated models, and field-key alignment, and correctness is validated through the focused MAG regression suites and the required non-perf functional regression gate.
**Constraints**: Preserve Hexagonal Architecture; keep enrichment business behavior unchanged; remove Field alias reliance for MAG contracts; update only new writes to `snake_case`; do not migrate historical MongoDB documents; preserve deterministic code generation and the custom post-generation MAG validator; satisfy strict clean-code and architecture review expectations  
**Scale/Scope**: Two MAG sample documents, two MAG JSON Schema contracts, two generated Pydantic modules, one router, one use case, one core mapper, two MongoDB repositories, and five MAG-focused test modules plus the full non-perf functional suite

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

- Architecture: PASS. The feature keeps validation in inbound schemas, orchestration in the
  existing use case, and persistence details in existing MongoDB adapters.
- Core purity: PASS. `src/core/` changes are limited to plain-dict field access in the existing
  MAG mapper and use case.
- Ports: PASS. No new external capability is introduced; existing repository and transaction ports
  remain valid.
- Specs-first: PASS. The feature spec exists under `specs/011-snake-case-mag-api/` before design
  work, and the authoritative MAG contract sources to be edited also live under `specs/`.
- Canonical contracts: PASS. This feature does not modify shared canonical schemas under
  `schemas/`. It updates service-local MAG endpoint contract sources under
  `specs/001-service-skeleton/contracts/` and synchronizes the generated Pydantic models that
  mirror them.
- Validation: PASS. Request validation remains exclusively in generated Pydantic schemas under
  `src/adapters/inbound/api/schemas/`.
- Errors: PASS. No new domain exception type or HTTP mapping is required; existing invalid-payload
  and domain-error behavior remains intact.
- Structure: PASS. The design reuses the existing `specs/`, `src/`, and `tests/` folders.

## Project Structure

### Documentation (this feature)

```text
specs/011-snake-case-mag-api/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── http-api.md
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
specs/
├── 001-service-skeleton/
│   └── contracts/
│       ├── micro_affinity_group.schema.json
│       └── micro_affinity_group_processed.schema.json
├── samples/
│   └── micro-affinity-group/
│       ├── micro-affinity-group.json
│       └── micro-affinity-group-relationships.json
└── 011-snake-case-mag-api/
    ├── plan.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    └── contracts/
        └── http-api.md

src/
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── routers/
│   │       │   └── micro_affinity_groups.py
│   │       └── schemas/
│   │           ├── micro_affinity_group.py
│   │           └── micro_affinity_group_processed.py
│   └── outbound/
│       └── mongodb/
│           ├── micro_affinity_group_repository.py
│           └── micro_affinity_group_processed_repository.py
├── core/
│   ├── domain/
│   │   └── micro_affinity_group_relationship_mapper.py
│   ├── use_cases/
│   │   └── upsert_micro_affinity_group.py
│   └── exceptions/
└── infrastructure/
    └── main.py

tests/
├── conftest.py
├── test_micro_affinity_group_relationship_mapper.py
├── test_micro_affinity_group_use_case.py
├── test_micro_affinity_groups_endpoint.py
├── test_micro_affinity_groups_persistence.py
└── test_perf_smoke_micro_affinity_groups.py
```

**Structure Decision**: Keep the migration inside the existing MAG contract, adapter, and test
surfaces. The authoritative request and response schemas remain under
`specs/001-service-skeleton/contracts/`, generated models remain under
`src/adapters/inbound/api/schemas/`, and only the existing MAG router, use case, mapper,
repositories, and MAG-specific tests are updated for `snake_case`. No folders, endpoints, ports,
or parallel compatibility pipelines are introduced.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. Validation stays in generated inbound schemas, business behavior stays in
  the existing core mapper/use case, and MongoDB write details stay in outbound adapters.
- Core purity: PASS. The design only changes string-key access inside pure Python dict handling.
- Ports: PASS. Existing repository and transaction ports remain unchanged.
- Specs-first: PASS. Research, plan, data model, contract notes, and quickstart are recorded under
  `specs/011-snake-case-mag-api/` before implementation.
- Canonical contracts: PASS. The implementation will update service-local MAG contract sources
  under `specs/001-service-skeleton/contracts/` and related sample docs under `specs/samples/`;
  no root `schemas/` change is needed.
- Validation: PASS. The route continues to rely on Pydantic models in
  `src/adapters/inbound/api/schemas/` for request rejection before the core executes.
- Errors: PASS. Existing error mapping remains valid because only field naming changes.
- Structure: PASS. The baseline folder structure remains intact.
