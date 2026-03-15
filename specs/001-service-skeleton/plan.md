# Implementation Plan: Service Architectural Skeleton

**Branch**: `001-service-skeleton` | **Date**: 2026-03-14 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-service-skeleton/spec.md`

## Summary

Scaffold the Dependency Graph Service’s baseline hexagonal structure and foundational wiring:
define a single application composition entry point, introduce core ports for MongoDB Atlas and
LDAP, enforce specs-first inbound validation aligned to `specs/`, and standardize global error
handling using RFC 7807 Problem Details.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic, PyMongo (MongoDB Atlas), LDAP3  
**Storage**: MongoDB Atlas (via PyMongo)   
**Testing**: pytest  
**Target Platform**: Server (development on macOS; deploy target not specified)  
**Project Type**: Web service (HTTP JSON API)  
**Performance Goals**: Not specified (skeleton/MVP)  
**Constraints**: Hexagonal Architecture boundaries; specs-first contracts; strict inbound validation;
app-singleton DI lifecycle for external clients; sync core ports/use cases  
**Scale/Scope**: Architectural skeleton only (health endpoint + minimal validation endpoint + minimal component retrieval endpoint + wiring + guardrails)

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
specs/001-service-skeleton/
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

**Structure Decision**: Adopt the constitution’s baseline structure exactly.

## Phase Outputs (Design Artifacts)

- Phase 0 (Research): `research.md`
- Phase 1 (Design): `data-model.md`, `contracts/`, `quickstart.md`

## Implementation Outline

1. Create all directories in the constitution’s baseline `specs/`, `src/`, and `tests/` tree.
2. Add a `pyproject.toml` defining the service package and dependencies, and generate a pinned `requirements.txt` lockfile (committed):
   - FastAPI + Pydantic for inbound API and validation.
   - PyMongo for MongoDB Atlas connectivity.
   - LDAP3 for LDAP integration.
   - pytest for testing.
3. Add `src/infrastructure/main.py` as the application entry point:
   - FastAPI application factory.
   - Startup/shutdown hooks.
   - Dependency wiring (DI) at the boundary.
4. Define core ports (ABCs) in `src/core/ports/`:
   - Graph repository port for persistence operations.
   - Identity provider port for authentication/user lookup.
   - Ports/use cases remain synchronous.
   - Ports expose minimal method sets required by the skeleton (stubs are acceptable), but method
     names/parameters should align with the domain model terms (component, dependency edge).
5. Implement minimal outbound adapter skeletons:
   - `src/adapters/outbound/mongodb/`: PyMongo client initialization + repository implementation
   - `src/adapters/outbound/ldap/`: LDAP3 connection setup + identity provider implementation
     placeholder methods.
   - Adapters use an app-singleton lifecycle: create on startup, reuse per request, close on
     shutdown.
6. Implement inbound API skeleton:
   - Establish authoritative contract artifacts under `specs/001-service-skeleton/contracts/`:
     - `openapi.yaml` is authoritative for the HTTP surface area.
     - `*.schema.json` files are authoritative for request/response shapes.
     - `http-api.md` and `problem-details.md` are explanatory/narrative docs and must remain consistent with the authoritative artifacts.
   - `src/adapters/inbound/api/routers/health.py` health-check router.
   - `src/adapters/inbound/api/schemas/` contains generated models (committed) derived from `specs/`.
   - `src/adapters/inbound/api/routers/component_validation.py` validation endpoint router.
   - `src/adapters/inbound/api/routers/components.py` minimal component retrieval router (for exercising domain error mapping).
7. Implement global error handling in `src/infrastructure/errors/`:
   - Exception handler registration.
   - Mapping from domain exceptions to HTTP status codes (per constitution).
   - RFC 7807 Problem Details response format (`application/problem+json`), with optional stable
     `error_code`.
   - Ensure validation errors are also represented as Problem Details.
8. Add CI guardrails:
   - Core purity import-boundary check (fails CI if `src/core/` imports forbidden libraries).
   - Schema/model drift check (fails CI if generated/committed Pydantic models are not in sync with
     `specs/`).

## Complexity Tracking

No constitution violations requiring justification.
