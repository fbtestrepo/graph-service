# Implementation Plan: Persist Components Payload

**Branch**: `003-persist-components-payload` | **Date**: 2026-03-21 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/003-persist-components-payload/spec.md`

## Summary

Extend the existing `POST /components` endpoint so that each successful request is persisted to
MongoDB before returning `200 OK`, while keeping the response body an exact echo of the submitted
JSON value (including non-object JSON root types). If persistence fails for any reason, the
endpoint MUST return `500 application/problem+json` and MUST NOT return `200`.

Design is ports-and-adapters:
- Inbound adapter remains responsible for parsing/validation of arbitrary JSON.
- Core adds a new port + use case to record the payload.
- Outbound MongoDB adapter implements the new port.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic v2, PyMongo  
**Storage**: MongoDB (configured via `GRAPH_SERVICE_MONGODB_URI` and `GRAPH_SERVICE_MONGODB_DATABASE`)  
**Testing**: pytest (integration tests with MongoDB running locally via Docker/testcontainers)  
**Target Platform**: Server (development on macOS; deploy target not specified)  
**Project Type**: Web service (HTTP JSON API)  
**Performance Goals**: Not specified (MVP behavior change only)  
**Constraints**: Hexagonal boundaries; core purity; specs-first contracts; persistence must occur
before `200 OK`; error responses must use RFC 7807 Problem Details; folder structure immutable  
**Scale/Scope**: Persist-and-echo behavior for `POST /components` only (no read/list APIs)

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
specs/003-persist-components-payload/
├── spec.md              # Feature spec (source requirements)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API + error contracts)
├── checklists/          # Spec checklists
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

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

**Structure Decision**: Add new persistence capability via a core port + use case and a MongoDB
outbound adapter, wired through `app.state` like the existing MongoDB adapters.

## Phase Outputs (Design Artifacts)

- Phase 0 (Research): `research.md`
- Phase 1 (Design): `data-model.md`, `contracts/`, `quickstart.md`

## Implementation Outline

1. Contracts-first documentation updates for persistence behavior:
   - Update `POST /components` documentation to explicitly call out the persistence side effect.
   - Ensure the OpenAPI contract documents a `500 application/problem+json` response for persistence
     failures.
2. Core additions (framework-agnostic):
   - Introduce a new port in `src/core/ports/` for persisting payload records.
   - Add a core use case in `src/core/use_cases/` that persists then returns the payload for echo.
3. Outbound adapter (MongoDB):
   - Implement the new port in `src/adapters/outbound/mongodb/` by inserting documents shaped like:
     `{ received_at: <utc datetime>, payload: <any JSON value> }`.
4. Inbound adapter (`POST /components`):
   - Call the new use case instead of directly echoing.
   - Preserve current behavior for 400/422 responses and logging truncation.
5. Error handling:
   - Any persistence exception must result in `500 application/problem+json` (no false `200`).
6. Tests:
   - Add integration tests that run MongoDB locally (Docker/testcontainers) and assert a record is
     inserted for both object and non-object JSON values.

## Complexity Tracking

No constitution violations requiring justification.
