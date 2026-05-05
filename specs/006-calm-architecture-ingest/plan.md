# Implementation Plan: CALM Architecture Document Ingestion

**Branch**: `006-calm-architecture-ingest` | **Date**: 2026-05-02 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/006-calm-architecture-ingest/spec.md`
**Input**: Feature specification from `/specs/006-calm-architecture-ingest/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build `POST /application-architectures` as a thin FastAPI inbound adapter that validates request
payloads against a generated Pydantic v2 model rooted in `schemas/calm/v1_2/calm.json`, with a
feature-specific contract wrapper that makes root `metadata` mandatory and enforces strict
`AssetID`, `version`, and `created` constraints. Persist accepted payloads through a new core port
and MongoDB adapter keyed by `metadata.AssetID` + `metadata.version`, returning `201 Created` on
first insert and `200 OK` on overwrite.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, pymongo, pydantic-settings, datamodel-code-generator, pytest, httpx/TestClient, testcontainers[mongodb]  
**Storage**: MongoDB Atlas / MongoDB collection `application-architectures` keyed by `metadata.AssetID` + `metadata.version`  
**Testing**: pytest with FastAPI `TestClient` for endpoint tests and testcontainers-backed MongoDB integration tests  
**Target Platform**: ASGI web service running locally on macOS/Linux and deployable to Linux server environments
**Project Type**: web-service  
**Performance Goals**: Meet SC-004: for valid submissions up to 1 MB, at least 95 of 100 sequential requests complete within 2 seconds in the test environment  
**Constraints**: Preserve Hexagonal Architecture; keep all JSON validation in inbound Pydantic models; use `schemas/calm/v1_2/calm.json` as the authoritative entry schema; return `400` for malformed JSON and `422` for schema/metadata violations; distinguish create vs overwrite with `201`/`200`; keep folder structure unchanged  
**Scale/Scope**: One new POST endpoint, one generated/wrapped request model, one new core repository port/use case, one MongoDB adapter, and focused endpoint/persistence tests

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

- Architecture: PASS. Router stays thin, business orchestration remains in a core use case, and
  MongoDB access remains inside an outbound adapter.
- Core purity: PASS. New persistence behavior is introduced through a core repository port rather
  than direct framework/driver imports in `src/core/`.
- Ports: PASS. The feature introduces a dedicated application architecture repository interface.
- Specs-first: PASS. Feature-specific HTTP contracts are planned under
  `specs/006-calm-architecture-ingest/contracts/`.
- Canonical contracts: PASS. `schemas/calm/v1_2/calm.json` remains the authoritative CALM entry
  contract; the feature only layers service-specific constraints on top.
- Validation: PASS. Request validation remains entirely in generated/wrapped Pydantic models under
  `src/adapters/inbound/api/schemas/`.
- Errors: PASS. Existing request validation handlers already classify malformed JSON as `400` and
  schema failures as `422`; no new domain exception is required for this feature.
- Structure: PASS. All planned files fit the existing baseline folders.

## Project Structure

### Documentation (this feature)

```text
specs/006-calm-architecture-ingest/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── application_architecture.schema.json
│   ├── http-api.md
│   └── openapi.yaml
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
schemas/
└── calm/
  └── v1_2/
    ├── calm.json
    ├── core.json
    ├── control.json
    ├── flow.json
    └── interface.json

specs/
└── 006-calm-architecture-ingest/
  └── contracts/
    ├── application_architecture.schema.json
    ├── http-api.md
    └── openapi.yaml

src/
├── core/
│   ├── ports/
│   │   └── application_architecture_repository.py
│   └── use_cases/
│       └── upsert_application_architecture.py
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── dependencies/
│   │       │   └── wiring.py          # add repository getter
│   │       ├── routers/
│   │       │   └── application_architectures.py
│   │       └── schemas/
│   │           ├── application_architecture.py
│   │           └── README.md          # update schema-to-model mapping
│   └── outbound/
│       └── mongodb/
│           └── application_architecture_repository.py
└── infrastructure/
  └── main.py                        # register router and repository on app state

tests/
├── test_application_architectures_endpoint.py
└── test_application_architectures_persistence.py
```

**Structure Decision**: Reuse the existing `components` endpoint pattern exactly: generate a
Pydantic boundary model in `src/adapters/inbound/api/schemas/`, introduce a dedicated repository
ABC in `src/core/ports/`, implement orchestration as a dataclass use case in
`src/core/use_cases/`, and isolate MongoDB persistence in `src/adapters/outbound/mongodb/`. Keep
canonical CALM schemas in `schemas/calm/v1_2/` and store only the service-specific wrapper schema
and OpenAPI working copy under `specs/006-calm-architecture-ingest/contracts/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. Design keeps HTTP parsing/validation in the inbound adapter, persistence in
  MongoDB adapter, and orchestration in a core use case.
- Core purity: PASS. The core only knows about repository abstractions and simple dataclass result
  types.
- Ports: PASS. The plan introduces `ApplicationArchitectureRepository` as the only core-to-storage
  contract.
- Specs-first: PASS. The feature defines a working OpenAPI contract and feature-local JSON Schema
  wrapper under `specs/006-calm-architecture-ingest/contracts/`.
- Canonical contracts: PASS. No canonical CALM schema is edited; `schemas/calm/v1_2/calm.json`
  remains the single source of truth for the entry contract.
- Validation: PASS. The plan keeps strict metadata enforcement in the generated/wrapped Pydantic
  request model under `src/adapters/inbound/api/schemas/`.
- Errors: PASS. Existing validation and problem-details infrastructure is reused without leaking
  stack traces.
- Structure: PASS. No new folders are introduced.
