# Implementation Plan: Micro Affinity Group Submission

**Branch**: `007-add-micro-affinity-endpoint` | **Date**: 2026-05-05 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/007-add-micro-affinity-endpoint/spec.md`
**Input**: Feature specification from `/specs/007-add-micro-affinity-endpoint/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build `POST /micro-affinity-groups` as a thin FastAPI inbound adapter that validates a
sample-derived micro affinity group payload through a generated Pydantic v2 model, then delegates
to a core use case that cross-validates each workload against the matching application
architecture record before upserting the payload into MongoDB. The use case will query the
`application-architectures` collection by `metadata.AssetID + metadata.version`, resolve `service`
nodes by `metadata.code-repo`, enforce the clarified `workload.asset-id -> metadata.asset-id` rule,
and persist accepted documents into `micro-affinity-groups` with `201 Created` on insert and
`200 OK` on overwrite.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, pymongo, pydantic-settings, datamodel-code-generator, pytest, httpx/TestClient, testcontainers[mongodb]  
**Storage**: MongoDB Atlas / MongoDB collection `micro-affinity-groups`, plus read access to `application-architectures` for cross-collection validation  
**Testing**: pytest with FastAPI `TestClient` for endpoint tests, focused use-case unit tests with fake repositories, and testcontainers-backed MongoDB integration tests  
**Target Platform**: ASGI web service running locally on macOS/Linux and deployable to Linux server environments
**Project Type**: web-service  
**Performance Goals**: Meet SC-005: for valid submissions up to 250 KB, at least 95 of 100 sequential requests complete within 2 seconds in the test environment  
**Constraints**: Preserve Hexagonal Architecture; keep all JSON shape/format validation in inbound Pydantic schemas; reject malformed JSON as `400`; reject schema and cross-collection validation failures as `422`; keep folder structure unchanged; follow the clarified `workload.asset-id -> resolved service node metadata.asset-id`  
**Scale/Scope**: One new POST endpoint, one new generated request model, one new repository port, one extension to the existing application-architecture port for lookup, one new core upsert use case, one new MongoDB adapter, and focused endpoint/use-case/persistence tests

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

- Architecture: PASS. The design keeps FastAPI routing thin, moves architectural alignment checks
  into a core use case, and keeps MongoDB reads/writes in outbound adapters.
- Core purity: PASS. Cross-collection validation will depend only on core repository abstractions
  and domain exceptions, not on framework or driver imports inside `src/core/`.
- Ports: PASS. The feature introduces a dedicated `MicroAffinityGroupRepository` port and extends
  the existing `ApplicationArchitectureRepository` with a lookup capability needed by the new
  business rule.
- Specs-first: PASS. The feature spec, clarifications, and working-copy contracts live under
  `specs/007-add-micro-affinity-endpoint/` before implementation changes.
- Canonical contracts: PASS. No canonical shared schema under `schemas/` changes are required;
  the new request contract is service-local and belongs under `specs/`.
- Validation: PASS. Structural validation remains in a generated/request-wrapped Pydantic model in
  `src/adapters/inbound/api/schemas/`, while cross-collection checks happen only after the payload
  is structurally valid.
- Errors: PASS. Cross-collection failures require new core exceptions mapped to `422` through the
  existing problem-details infrastructure.
- Structure: PASS. All planned files fit the constitution’s baseline folders.

## Project Structure

### Documentation (this feature)

```text
specs/007-add-micro-affinity-endpoint/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── micro_affinity_group.schema.json
│   ├── http-api.md
│   └── openapi.yaml
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
specs/
├── 001-service-skeleton/
│   └── contracts/
│       ├── micro_affinity_group.schema.json   # implementation-time authoritative codegen source
│       ├── http-api.md                        # updated service contract index
│       └── openapi.yaml                       # updated service working contract
└── 007-add-micro-affinity-endpoint/
    └── contracts/
        ├── micro_affinity_group.schema.json   # planning-time working copy
        ├── http-api.md
        └── openapi.yaml

src/
├── core/
│   ├── ports/
│   │   ├── application_architecture_repository.py
│   │   └── micro_affinity_group_repository.py
│   ├── use_cases/
│   │   └── upsert_micro_affinity_group.py
│   └── exceptions/
│       ├── application_architecture_not_found.py
│       └── micro_affinity_group_workload_mismatch.py
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── dependencies/
│   │       │   └── wiring.py                  # add repository getter(s)
│   │       ├── routers/
│   │       │   └── micro_affinity_groups.py
│   │       └── schemas/
│   │           ├── micro_affinity_group.py
│   │           └── README.md                  # update schema-to-model mapping
│   └── outbound/
│       └── mongodb/
│           ├── application_architecture_repository.py
│           └── micro_affinity_group_repository.py
├── infrastructure/
│   ├── errors/
│   │   ├── handlers.py
│   │   └── mappers.py
│   └── main.py

generate_inbound_models.sh

tests/
├── test_micro_affinity_group_use_case.py
├── test_micro_affinity_groups_endpoint.py
└── test_micro_affinity_groups_persistence.py
```

**Structure Decision**: Reuse the existing components/application-architectures pattern exactly:
keep the router in `src/adapters/inbound/api/routers/`, perform cross-collection business
orchestration in a single core use case, isolate MongoDB access behind repository ports, and keep
generated/request-wrapped schemas in `src/adapters/inbound/api/schemas/`. The planning artifacts
live under `specs/007-add-micro-affinity-endpoint/contracts/`, while implementation is expected to
promote the final authoritative codegen source into `specs/001-service-skeleton/contracts/` so the
existing codegen/CI workflow remains coherent.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. Design keeps request parsing in the inbound adapter, cross-collection
  alignment in the core use case, and all collection access in MongoDB adapters.
- Core purity: PASS. The core only depends on repository ports and domain exceptions/result types.
- Ports: PASS. The plan introduces one new repository port and extends the existing architecture
  repository port with a read lookup needed for validation.
- Specs-first: PASS. Feature-local contract, data model, research, and quickstart all live under
  `specs/007-add-micro-affinity-endpoint/` before code changes.
- Canonical contracts: PASS. No root `schemas/` update is required because this endpoint contract
  is service-local rather than canonical/shared.
- Validation: PASS. Pydantic handles all JSON shape/format checks before the use case runs, and
  the use case handles only repository-backed business validation.
- Errors: PASS. New domain exceptions are explicitly planned for architecture-missing and
  workload-mismatch conditions and will be mapped to `422` without leaking stack traces.
- Structure: PASS. No new folders are introduced.
