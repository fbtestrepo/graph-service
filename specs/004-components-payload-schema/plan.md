# Implementation Plan: Components Payload Validation & MongoDB Upsert

**Branch**: `004-components-payload-schema` | **Date**: 2026-03-24 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/004-components-payload-schema/spec.md`

## Summary

Introduce a strict request schema for `POST /components` based on the provided sample payload.
The endpoint validates required fields (`node-id`, `node-type`, `node-name`, `metadata.parent-asset-id`) and optional arrays (`interfaces`, `relationships`) at the inbound boundary via Pydantic models generated from JSON Schema.

On success, the service upserts the payload into MongoDB keyed by `node-id`:
- returns `201 Created` when a new `node-id` is inserted
- returns `200 OK` when an existing `node-id` is replaced

Malformed JSON returns `400 application/problem+json`; schema/constraint validation errors return `422 application/problem+json`.

Design remains ports-and-adapters:
- Inbound adapter handles parsing/validation and HTTP response mapping.
- Core coordinates upsert behavior via a port.
- Outbound MongoDB adapter implements upsert using `replace_one(..., upsert=True)`.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, PyMongo  
**Storage**: MongoDB (configured via `GRAPH_SERVICE_MONGODB_URI` and `GRAPH_SERVICE_MONGODB_DATABASE`)  
**Testing**: pytest (integration tests use MongoDB via testcontainers/Docker)  
**Target Platform**: Server (development on macOS; deploy target not specified)
**Project Type**: Web service (HTTP JSON API)  
**Performance Goals**: Keep request handling responsive; success criteria targets 95/100 requests within 1s in a local test run  
**Constraints**: Hexagonal boundaries; specs-first contracts; inbound validation before core; no core framework/driver imports; Problem Details for errors; folder structure immutable  


**Scale/Scope**: Contract + persistence behavior change for `POST /components` and `GET /components/{component_id}` (treat `{component_id}` as `node-id`) (and related schemas/tests)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Required gates for this project (see `.specify/memory/constitution.md`):

- Architecture: Feature design preserves Hexagonal Architecture (Ports & Adapters).
- Core purity: `src/core/` remains framework-agnostic (no `fastapi`, `pymongo`/`motor`, `ldap3`, etc.).
- Ports: Any new external capability is introduced as an ABC in `src/core/ports/`.
- Specs-first: Any API contract change starts in `specs/` (OpenAPI + JSON Schemas).
- Validation: Inbound adapter validates all JSON payloads via Pydantic schemas in
  `src/adapters/inbound/api/schemas/` before calling core use cases.
- Errors: New domain exceptions are defined in `src/core/exceptions/` and mapped to HTTP in
  `src/infrastructure/errors/` without leaking stack traces.
- Structure: Folder structure remains unchanged unless explicitly approved.

**Gate Evaluation (pre-research)**: PASS (no violations)  
**Gate Evaluation (post-design)**: PASS (no violations)

## Project Structure

### Documentation (this feature)

```text
specs/004-components-payload-schema/
├── spec.md              # Feature spec (source requirements)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API + schema working copy)
├── checklists/          # Spec checklists
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# Authoritative baseline structure (DO NOT change folders without explicit approval)

specs/

src/
├── core/
│   ├── domain/
│   ├── ports/
│   ├── use_cases/
│   └── exceptions/
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── dependencies/
│   │       ├── routers/
│   │       └── schemas/
│   └── outbound/
│       ├── mongodb/
│       └── ldap/
└── infrastructure/
  ├── config/
  ├── errors/
  ├── middleware/
  └── main.py

tests/
```

**Structure Decision**: Implement the new behavior as a boundary validation + core use case +
MongoDB adapter change, without introducing any new top-level folders.

## Phase Outputs (Design Artifacts)

- Phase 0 (Research): `research.md`
- Phase 1 (Design): `data-model.md`, `contracts/`, `quickstart.md`

## Implementation Outline

1. Contracts-first updates:
  - Define a new JSON Schema for `POST /components` (component node payload).
  - Update OpenAPI for `/components` to return `201`/`200` with the same schema.
2. Inbound validation:
  - Generate a Pydantic v2 schema from the new JSON Schema into `src/adapters/inbound/api/schemas/`.
  - Update the `/components` router to accept the new schema type instead of `JsonValue`.
3. Core use case + port:
  - Update (or replace) the existing “record payload” use case to perform an upsert keyed by `node-id`.
  - Update the core port to support upsert and return whether the operation created or updated.
4. MongoDB adapter:
  - Implement upsert using `replace_one(..., upsert=True)` and determine created vs updated.
5. HTTP response behavior:
  - Return `201` on create and `200` on update.
  - Preserve existing Problem Details behavior for `400` malformed JSON and `422` validation errors.
6. Tests:
  - Update endpoint tests to reflect object-only payloads and 200/201 behavior.
  - Update Mongo integration tests to assert replacement semantics (no document count increase on update).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations requiring justification.
