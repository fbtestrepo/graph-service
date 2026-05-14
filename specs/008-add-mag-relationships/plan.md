# Implementation Plan: Micro Affinity Group Relationship Enrichment

**Branch**: `008-add-mag-relationships` | **Date**: 2026-05-06 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/008-add-mag-relationships/spec.md`
**Input**: Feature specification from `/specs/008-add-mag-relationships/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Enhance `POST /micro-affinity-groups` so each accepted submission is processed in a transactional
pipeline that preserves the existing raw-record write, computes a relationship-enriched variant of
the document, and upserts that transformed document into `micro-affinity-groups-processed`.
The endpoint remains a thin FastAPI adapter with the existing input contract, while a new core
relationship-mapping service computes the `relationships` list from application-architecture
nodes and edges. MongoDB session-backed transactions will wrap the raw write, transformation read
path, and processed upsert so failures roll back the whole unit of work, and the response body
will return the stored processed document shown by the relationship sample.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, pymongo, pydantic-settings, datamodel-code-generator, pytest, httpx/TestClient, testcontainers[mongodb], Python standard-library `logging`  
**Storage**: MongoDB Atlas / MongoDB collections `micro-affinity-groups` (raw input), `micro-affinity-groups-processed` (transformed output), plus read access to `application-architectures` for transformation lookups  
**Testing**: pytest with FastAPI `TestClient`, fake-repository/use-case unit tests, and replica-set-capable MongoDB integration tests via testcontainers  
**Target Platform**: ASGI web service running locally on macOS/Linux and deployable to Linux server environments
**Project Type**: web-service  
**Performance Goals**: Preserve existing endpoint behavior without material regression and keep valid sequential submissions within the existing service envelope while dual-write transformation is enabled  
**Constraints**: Preserve Hexagonal Architecture; keep request validation in inbound Pydantic schemas; preserve existing raw-input persistence behavior; wrap raw persist + transformation + processed upsert in one MongoDB transaction; log each relationship search result; reject missing architecture/source/destination-service lookups as `422`; leave workloads with zero relationships non-fatal; keep folder structure unchanged  
**Scale/Scope**: One endpoint enhancement, one new processed response contract/model, one pure transformation component, one processed-document repository, one transaction manager port/adapter, session-aware repository updates, and focused regression/rollback/idempotency tests

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

- Architecture: PASS. The design keeps FastAPI routing thin, isolates relationship generation in a
  dedicated core mapper/service, and leaves MongoDB access plus transactions in outbound adapters.
- Core purity: PASS. The core will depend only on repository/transaction ports, pure domain
  exceptions, and standard-library logging.
- Ports: PASS. The new processed-write capability and transactional session boundary will be
  introduced through core ports rather than direct driver access.
- Specs-first: PASS. The clarified feature spec exists under `specs/008-add-mag-relationships/`
  before design and implementation changes.
- Canonical contracts: PASS. This endpoint change is service-local, so the new response contract
  belongs under `specs/` and not root `schemas/`.
- Validation: PASS. The request shape remains validated by inbound Pydantic models before core
  transformation logic runs.
- Errors: PASS. Missing architecture, missing source service, and unresolved destination-service
  failures remain domain exceptions mapped to `422`.
- Structure: PASS. The planned additions fit the baseline directories without creating new
  folders.

## Project Structure

### Documentation (this feature)

```text
specs/008-add-mag-relationships/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── micro_affinity_group_processed.schema.json
│   ├── http-api.md
│   └── openapi.yaml
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
specs/
├── 001-service-skeleton/
│   └── contracts/
│       ├── micro_affinity_group.schema.json             # existing authoritative request contract
│       ├── micro_affinity_group_processed.schema.json   # new authoritative response contract
│       ├── http-api.md                                  # updated service contract index
│       └── openapi.yaml                                 # updated service working contract
└── 008-add-mag-relationships/
    └── contracts/
        ├── micro_affinity_group_processed.schema.json   # planning-time processed response schema
        ├── http-api.md
        └── openapi.yaml

src/
├── core/
│   ├── domain/
│   │   └── micro_affinity_group_relationship_mapper.py
│   ├── ports/
│   │   ├── application_architecture_repository.py
│   │   ├── micro_affinity_group_repository.py
│   │   ├── micro_affinity_group_processed_repository.py
│   │   └── transaction_manager.py
│   ├── use_cases/
│   │   └── upsert_micro_affinity_group.py
│   └── exceptions/
│       ├── application_architecture_not_found.py
│       ├── micro_affinity_group_relationship_resolution_error.py
│       └── micro_affinity_group_workload_mismatch.py
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── dependencies/
│   │       │   └── wiring.py
│   │       ├── routers/
│   │       │   └── micro_affinity_groups.py
│   │       └── schemas/
│   │           ├── micro_affinity_group.py
│   │           ├── micro_affinity_group_processed.py
│   │           └── README.md
│   └── outbound/
│       └── mongodb/
│           ├── application_architecture_repository.py
│           ├── micro_affinity_group_processed_repository.py
│           ├── micro_affinity_group_repository.py
│           └── transaction_manager.py
├── infrastructure/
│   ├── errors/
│   │   ├── handlers.py
│   │   └── mappers.py
│   └── main.py

generate_inbound_models.sh

tests/
├── test_micro_affinity_group_relationship_mapper.py
├── test_micro_affinity_group_use_case.py
├── test_micro_affinity_groups_endpoint.py
└── test_micro_affinity_groups_persistence.py
```

**Structure Decision**: Extend the existing micro-affinity endpoint rather than creating a second
workflow. Keep request parsing and response serialization in the inbound adapter, place the
relationship-transformation logic in a dedicated pure core mapper, orchestrate raw-write +
transformation + processed-upsert in the existing micro-affinity use case, isolate MongoDB
transaction/session behavior in outbound adapters behind ports, and add a processed response schema
to the existing codegen path so the response contract stays spec-driven.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. The design keeps routing thin, transformation logic pure in `src/core/`,
  and persistence/transaction control in MongoDB adapters.
- Core purity: PASS. The core remains free of `fastapi`, `pymongo`, and other driver imports.
- Ports: PASS. The processed-document repository and transaction boundary are introduced as core
  ports before adapter implementation.
- Specs-first: PASS. Feature-local research, data model, contracts, and quickstart all live under
  `specs/008-add-mag-relationships/` before code changes.
- Canonical contracts: PASS. The processed response schema is service-local and belongs under
  `specs/`, not `schemas/`.
- Validation: PASS. Existing inbound request validation remains in generated/wrapped Pydantic
  models; the transformation mapper runs only after the request is structurally valid.
- Errors: PASS. Destination-resolution failures are modeled as domain exceptions and continue to
  map through the existing problem-details infrastructure.
- Structure: PASS. No new folders are introduced.
