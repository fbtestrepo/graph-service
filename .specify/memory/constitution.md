<!--
Sync Impact Report

- Version change: 1.1.0 -> 1.2.0
- Modified principles:

  - III. Domain Errors & HTTP Classification
  - Workflow & Quality Gates
  - Governance
- Added sections:

  - None
- Removed sections:

  - None
- Templates requiring updates:

  - ✅ updated: .specify/templates/plan-template.md
  - ✅ updated: .specify/templates/spec-template.md
  - ✅ updated: .specify/templates/tasks-template.md
  - ✅ updated: .specify/templates/checklist-template.md
  - ✅ verified: .specify/templates/commands/ is not present in this repository
- Deferred TODOs:

  - None
-->

# Dependency Graph Service API Constitution

## Core Principles

### I. Hexagonal Architecture (Ports & Adapters)
This service strictly adheres to Hexagonal Architecture. The primary objective is absolute
isolation between business logic and external delivery mechanisms, databases, and third-party
services.

Non-negotiables:
- Dependencies MUST point inward toward the core (Dependency Rule).
- The `src/core/` directory MUST be framework-agnostic and infrastructure-agnostic.
- Inbound adapters (e.g., FastAPI) MUST call core use cases; they MUST NOT contain business rules.
- Outbound adapters (e.g., MongoDB, LDAP) MUST implement core ports; they MUST NOT be called
  directly by core domain code.

Rationale: Preserves testability and allows swapping delivery/persistence/auth without rewriting
core logic.

### II. Specification-Driven API Contracts & Validation
This service uses Specification-Driven Development (SDD). The `specs/` directory is the single
source of truth for feature intent, behavioral requirements, and software specifications. The
root-level `schemas/` directory is the single source of truth for canonical data contracts
(e.g., CALM JSON Schemas).

Non-negotiables:
- Any change to feature intent, behavioral requirements, or software specifications MUST start by
  updating `specs/` first.
- Any change to canonical or shared data contracts MUST start by updating `schemas/` first.
- All JSON payload validation is the exclusive responsibility of the inbound adapter layer.
- Pydantic models in `src/adapters/inbound/api/schemas/` MUST strictly mirror the applicable
  authoritative contracts defined under `specs/` and/or `schemas/`, and their source path MUST be
  documented.
- Invalid payloads MUST be rejected before reaching core use cases, using:
  - `422 Unprocessable Entity` for schema/validation errors
  - `400 Bad Request` for malformed requests that cannot be interpreted

Rationale: Prevents contract drift by separating feature specification ownership from canonical
data contract ownership while keeping the core free of transport concerns.

### III. Domain Errors & HTTP Classification
Business logic failures MUST be represented as domain exceptions and MUST NOT leak HTTP concerns
into the core.

Non-negotiables:
- Domain/business exceptions (e.g., `CircularDependencyDetected`, `ComponentNotFound`) MUST be
  custom Python exceptions defined in `src/core/exceptions/`.
- Domain exceptions MUST contain pure context and MUST NOT contain HTTP status codes or
  HTTP-specific terminology.
- Domain exceptions MUST be caught by global exception handlers in `src/infrastructure/errors/`
  and mapped to semantically correct HTTP responses.
- For graph-traversal or graph-resolution endpoints, `404 Not Found` MUST be reserved strictly for
  the primary resource identifier supplied directly in the URL path being absent from the
  authoritative persistence store.
- For graph-traversal or graph-resolution endpoints, once the primary path resource is confirmed to
  exist, any failure to resolve, traverse, or construct the downstream graph because required
  intermediate or dependent records are missing, stale, unsynced, or corrupted MUST raise a
  structured domain validation exception that maps to `422 Unprocessable Entity`, not `404`.
- Stack traces and internal error details MUST NOT be returned to clients.

Required HTTP classification:
- `400 Bad Request`: Malformed business logic requests.
- `401 Unauthorized`: Failed LDAP authentication.
- `403 Forbidden`: Insufficient LDAP authorization/roles.
- `404 Not Found`: The primary resource identified directly by the request path does not exist in
  MongoDB.
- `409 Conflict`: State conflicts (e.g., attempting to create a duplicate edge).
- `422 Unprocessable Entity`: Schema/validation failures, or graph/data-integrity failures where
  the primary resource exists but downstream resolution cannot be completed consistently.
- `500 Internal Server Error`: Unhandled adapter/infrastructure failures.

Rationale: Keeps the domain model portable while providing a predictable REST error contract.

### IV. External Integrations Are Adapters
All external system interactions MUST live in outbound adapters and MUST implement core ports.

Non-negotiables:
- Authentication and directory lookups MUST be handled via LDAP.

  - Concrete LDAP querying MUST reside exclusively in `src/adapters/outbound/ldap/`.
  - The LDAP adapter MUST implement the authentication port defined in the core.
- Persistence MUST use MongoDB Atlas.

  - Concrete MongoDB data access logic (drivers like `pymongo`/`motor`) MUST reside exclusively in
    `src/adapters/outbound/mongodb/`.
  - MongoDB adapters MUST implement repository ports defined in the core.

Rationale: Prevents infrastructure details from contaminating the core and enables testing via
port fakes/mocks.

### V. Immutable Project Structure
The project structure below is the authoritative blueprint for this service.

Non-negotiables:
- AI agents and developers MUST NOT modify, add, remove, or rename folders from the baseline

  structure without explicit permission from the lead architect.
- The core (`src/core/`) MUST NOT import operational/framework libraries (examples include

  `fastapi`, `pymongo`, `motor`, `ldap3`).
- All communication between the core and external systems MUST be defined by Abstract Base

  Classes (ABCs) located in `src/core/ports/`.

Rationale: Enforces architectural boundaries and keeps the codebase navigable.

## Authoritative Structure Blueprint

The following directory structure is the baseline and MUST be treated as immutable.

Directory map and purposes:

```text
graph_service/
+-- specs/                  # Source of truth for feature intent, behavioral requirements, and software specifications.
+-- schemas/                # Source of truth for canonical data contracts (e.g., CALM JSON Schemas).
+-- src/
¦   +-- core/               # The heart of the application. Strictly framework-agnostic.
¦   ¦   +-- domain/         # Pure Python entities representing nodes, edges, dependencies.
¦   ¦   +-- ports/          # ABC interfaces defining inbound/outbound contracts.
¦   ¦   +-- use_cases/      # Application orchestration; coordinates domain + ports.
¦   ¦   +-- exceptions/     # Domain exceptions (pure context, no HTTP terms).
¦   ¦
¦   +-- adapters/           # Concrete implementations of ports.
¦   ¦   +-- inbound/
¦   ¦   ¦   +-- api/        # FastAPI application layer.
¦   ¦   ¦       +-- dependencies/ # FastAPI dependency injection helpers.
¦   ¦   ¦       +-- routers/      # HTTP endpoints mapping routes to use cases.
¦   ¦   ¦       +-- schemas/      # Pydantic models mirroring authoritative contracts.
¦   ¦   +-- outbound/
¦   ¦       +-- mongodb/    # MongoDB Atlas clients + repository implementations.
¦   ¦       +-- ldap/       # LDAP auth + user lookup implementations.
¦   ¦
¦   +-- infrastructure/     # Assembly and wiring.
¦       +-- config/         # Env loading, config models, DI container setup.
¦       +-- errors/         # Global exception handlers mapping core exceptions to HTTP.
¦       +-- middleware/     # Cross-cutting request/response concerns.
¦       +-- main.py         # FastAPI app factory / ASGI entrypoint.
+-- tests/                  # Test suites mapped to the architecture.
+-- pyproject.toml          # Project metadata.
+-- requirements.txt        # Locked dependencies.
```

## Workflow & Quality Gates

Delivery expectations for all changes:

- Specs-first: any change to feature intent, behavioral requirements, or software specifications
  MUST update `specs/` before code is implemented.
- Canonical-contracts-first: any change to canonical data contracts MUST update `schemas/`
  before generated models or adapter code are changed.
- Architecture boundaries: new business rules MUST go to `src/core/domain/` and/or

  `src/core/use_cases/`; adapters MUST remain thin.
- Ports-first: any new external integration capability MUST be introduced as a port in

  `src/core/ports/` and implemented in an adapter.
- Validation-first (inbound): requests MUST be validated in

  `src/adapters/inbound/api/schemas/` before calling core use cases.
- Error mapping: any new domain exception MUST be mapped in `src/infrastructure/errors/`.
- Traversal error semantics: graph-traversal endpoints MUST return `404` only when the primary
  path resource does not exist; once that resource exists, downstream graph-resolution failures
  MUST return `422` via structured domain exceptions.
- No core framework imports: review MUST confirm `src/core/` stays free of framework/driver

  imports.

## Governance
This constitution supersedes local conventions, ad-hoc patterns, and individual preferences.

Amendment procedure:
- Amendments MUST be made via PR that includes:

  - Rationale for the change
  - Migration notes if the change affects existing code
  - Updates to `.specify/templates/*` when they reference constitution requirements
- The lead architect (or explicitly delegated reviewer) MUST approve any amendment.

Versioning policy:
- The constitution uses semantic versioning (MAJOR.MINOR.PATCH).

  - MAJOR: backward-incompatible governance/architecture changes (e.g., removing hexagonal
    boundaries or redefining core vs adapter responsibilities)
  - MINOR: new principle/section added or materially expanded guidance
  - PATCH: clarifications, wording, typos, non-semantic refinements

Compliance expectations:
- Every feature plan and PR review MUST include a “Constitution Check” confirming:

  - Hexagonal boundaries remain intact
  - `specs/` is updated when feature intent, behavioral requirements, or software specifications
    change
  - `schemas/` is updated when canonical data contracts change
  - Inbound validation rejects invalid payloads before the core
  - Domain exceptions are mapped to correct HTTP responses
  - Graph-traversal endpoints reserve `404` for missing path resources and use `422` for
    downstream resolution failures after root existence is confirmed
  - Folder structure remains unchanged unless explicitly approved

**Version**: 1.2.0 | **Ratified**: 2026-03-14 | **Last Amended**: 2026-05-17
