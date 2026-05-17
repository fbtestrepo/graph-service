# Implementation Plan: MAG Upsert Uniqueness

**Branch**: `012-mag-upsert-uniqueness` | **Date**: 2026-05-17 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/012-mag-upsert-uniqueness/spec.md`
**Input**: Feature specification from `/specs/012-mag-upsert-uniqueness/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Change the Micro-AG write path so raw and processed MongoDB documents are identified by
`micro_ag_id + environment` instead of `micro_ag_id + environment + architecture_version`, while
keeping `architecture_version` required for request validation and for application-architecture
enrichment lookup. The plan keeps the existing endpoint, use case, and transaction boundary, but
cleans up the repository port contract to match the new identity, adds deterministic duplicate
detection for pre-existing conflicting records, maps that conflict to `409 Conflict`, and updates
MAG-focused tests plus the required non-perf regression suite to prove overwrite semantics, environment isolation, and unchanged validation behavior.

## Technical Context

**Language/Version**: Python 3.12+ (active workspace venv previously verified on Python 3.14.3)  
**Primary Dependencies**: FastAPI, Pydantic v2, pymongo, pytest, FastAPI TestClient/httpx, testcontainers[mongodb], ldap3, datamodel-code-generator  
**Storage**: MongoDB Atlas in production; MongoDB replica-set container for persistence-backed tests  
**Testing**: pytest with focused MAG suites plus required non-perf regression via `python -m pytest tests -v -k "not perf_smoke"`; architecture guard via `python check_core_purity.py`  
**Target Platform**: ASGI web service for macOS/Linux development and Linux server deployment
**Project Type**: web-service  
**Performance Goals**: No new throughput target. Preserve current MAG request behavior and keep the required non-perf regression suite green without introducing regression loops or new hot-path database round trips beyond one bounded identity-count check per collection inside the transaction.  
**Constraints**: Preserve Hexagonal Architecture; keep `architecture_version` required and still used for architecture lookup; do not manage MongoDB indexes in application code; reject duplicate pre-existing identity pairs with `409 Conflict`; fully replace stored raw and processed documents on overwrite; keep folder structure unchanged; satisfy strict architecture/code-review audit expectations.  
**Scale/Scope**: One POST endpoint, two generated Pydantic schema modules, two core repository ports, one use case, two MongoDB adapters, one domain-exception mapping path, and MAG-focused endpoint/use-case/persistence/perf tests plus the required non-perf regression suite.

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

- Architecture: PASS. The feature stays within the existing MAG router -> use case -> repository
  path and preserves the transaction boundary.
- Core purity: PASS. The core will own duplicate-identity decisions and created-vs-updated status
  derivation without importing MongoDB or FastAPI concerns.
- Ports: PASS. Repository interfaces are the right place to expose any new identity-count
  capability needed by the use case.
- Specs-first: PASS. Feature intent and clarifications are already captured under
  `specs/012-mag-upsert-uniqueness/` before design work.
- Canonical contracts: PASS. This feature does not change shared schemas under `schemas/`; any
  contract wording adjustments remain in service-local MAG artifacts under `specs/`.
- Validation: PASS. Request validation remains in the inbound Pydantic schemas; the feature does
  not move validation into the core.
- Errors: PASS. The planned duplicate-identity failure will use a new domain exception mapped to
  `409 Conflict` in the infrastructure error layer.
- Structure: PASS. The design reuses existing files and folders only.

## Project Structure

### Documentation (this feature)

```text
specs/012-mag-upsert-uniqueness/
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
├── 012-mag-upsert-uniqueness/
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   └── contracts/
│       └── http-api.md

src/
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── routers/
│   │       │   └── micro_affinity_groups.py
│   │       └── schemas/
│   │           ├── README.md
│   │           ├── micro_affinity_group.py
│   │           └── micro_affinity_group_processed.py
│   └── outbound/
│       └── mongodb/
│           ├── micro_affinity_group_repository.py
│           └── micro_affinity_group_processed_repository.py
├── core/
│   ├── exceptions/
│   ├── ports/
│   │   ├── micro_affinity_group_repository.py
│   │   └── micro_affinity_group_processed_repository.py
│   └── use_cases/
│       └── upsert_micro_affinity_group.py
└── infrastructure/
    └── errors/
        ├── handlers.py
        └── mappers.py

tests/
├── test_micro_affinity_group_use_case.py
├── test_micro_affinity_groups_endpoint.py
├── test_micro_affinity_groups_persistence.py
└── test_perf_smoke_micro_affinity_groups.py
```

**Structure Decision**: Keep the feature inside the existing MAG endpoint, use case, repository,
and test surfaces. The plan does not introduce new folders or parallel pipelines. Any contract or
schema wording changes stay under `specs/`, runtime validation remains in the generated inbound
schema modules, duplicate-identity detection is expressed through existing core ports and a new
domain exception, and MongoDB-specific lookup changes remain confined to the outbound adapters.

## Phase Plan

### Phase 0 - Contract And Identity Audit

- Confirm that the externally visible MAG payload shape remains the snake_case contract introduced
  by feature 011 and that the only behavioral change is identity semantics.
- Inspect `specs/001-service-skeleton/contracts/`, generated inbound schema modules, and
  `src/adapters/inbound/api/schemas/README.md` for any references that still imply
  `architecture_version` is part of the persistence identity.
- Record any needed contract wording changes in feature-local docs and determine whether the source
  JSON Schemas need description-only updates followed by model regeneration.

### Phase 1 - Boundary And Model Alignment

- Keep `architecture_version` in both inbound and outbound Pydantic models as a required field and
  preserve existing validation patterns and response shape.
- If the authoritative contract files under `specs/001-service-skeleton/contracts/` or the schema
  README mention the old three-field identity, update that wording and regenerate
  `src/adapters/inbound/api/schemas/micro_affinity_group.py` and
  `src/adapters/inbound/api/schemas/micro_affinity_group_processed.py` via
  `./generate_inbound_models.sh`.
- Verify that the router continues to accept and emit snake_case payloads without introducing any
  `architecture_version`-driven uniqueness logic at the API boundary.

### Phase 2 - Core And Repository Identity Rewrite

- Update `src/core/ports/micro_affinity_group_repository.py` and
  `src/core/ports/micro_affinity_group_processed_repository.py` so their API reflects the new
  MAG write-identity pair rather than the old three-field tuple. The preferred design is:
  - remove `architecture_version` from `upsert(...)` parameters because it is no longer part of the
    write identity;
  - add a small query capability such as `count_by_identity(micro_ag_id, environment, session)` so
    the core use case can detect `0`, `1`, or `>1` matches without depending on MongoDB details.
- Update `src/core/use_cases/upsert_micro_affinity_group.py` to:
  - derive identity from `micro_ag_id + environment` only for write operations;
  - keep using `architecture_version` for `ApplicationArchitectureRepository`
    `get_by_asset_id_and_version(...)` enrichment lookup;
  - perform duplicate detection for both raw and processed repositories inside the transaction
    before writing;
  - raise a new domain exception, e.g. `DuplicateMicroAffinityGroupIdentity`, if either collection
    reports more than one existing match for the pair;
  - compute the `created` flag from pre-upsert counts so `201` means the identity pair was absent
    and `200` means it already existed, regardless of whether `architecture_version` changed.
- Update `src/adapters/outbound/mongodb/micro_affinity_group_repository.py` and
  `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py` to:
  - narrow MongoDB filters from `{micro_ag_id, environment, architecture_version}` to
    `{micro_ag_id, environment}`;
  - keep full-document replacement semantics via `replace_one(..., upsert=True, session=session)`;
  - implement the new identity-count method using the same two-field filter;
  - exclude any index creation, index migration, or index validation logic from application code.
- Add the new domain exception under `src/core/exceptions/` and map it to `409 Conflict` in
  `src/infrastructure/errors/mappers.py` and `src/infrastructure/errors/handlers.py`.

### Phase 3 - Pytest Synchronization And Integration Validation

- Update MAG test doubles in `tests/test_micro_affinity_group_use_case.py`,
  `tests/test_micro_affinity_groups_endpoint.py`, and
  `tests/test_perf_smoke_micro_affinity_groups.py` so fake repository storage is keyed by
  `(micro_ag_id, environment)` rather than by the old three-field tuple.
- Update persistence assertions in `tests/test_micro_affinity_groups_persistence.py` to query by
  `micro_ag_id + environment` only while still asserting that the stored documents retain the new
  `architecture_version` value.
- Add or revise focused tests to prove:
  - same `micro_ag_id + environment` with a different `architecture_version` now returns `200 OK`
    and fully overwrites both raw and processed documents;
  - same `micro_ag_id` with a different `environment` still coexists and returns `201 Created` for
    the new environment;
  - duplicate pre-seeded raw or processed records for the same identity pair return
    `409 Conflict` with the mapped problem-details error code;
  - partial existing state in only one MAG collection is repaired through the normal transactional
    overwrite path;
  - processed-write failure still rolls back both collections.
- Synchronize any database seeding helpers or mock collection setup used in endpoint and
  persistence-backed tests so they no longer assume `architecture_version` is part of the write
  identity.
- Run validation in this order:
  - focused MAG suites during implementation;
  - `python check_core_purity.py` to protect architecture boundaries;
  - required non-perf regression suite `python -m pytest tests -v -k "not perf_smoke"` to satisfy
    the feature’s integration-testing requirement and prove there are no regression loops.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. The design keeps business decisions in the use case and confines MongoDB
  query mechanics to the repositories.
- Core purity: PASS. The core remains free of framework and driver imports; duplicate handling is a
  domain decision expressed through ports and a core exception.
- Ports: PASS. The plan updates existing repository ABCs rather than bypassing them.
- Specs-first: PASS. Research, data model, quickstart, and contract notes are all captured under
  `specs/012-mag-upsert-uniqueness/` before implementation.
- Canonical contracts: PASS. No root `schemas/` changes are required because the public MAG field
  shape remains unchanged.
- Validation: PASS. Inbound Pydantic validation remains the first boundary for malformed payloads.
- Errors: PASS. The plan adds a domain exception plus explicit HTTP mapping for the new conflict
  behavior.
- Structure: PASS. The baseline folder structure remains intact.
