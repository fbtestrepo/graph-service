<!--
Sync Impact Report

- Version change: unversioned template -> 1.0.0
- Modified principles:

  - (template placeholders) -> I. Hexagonal Architecture (Ports & Adapters)
  - (template placeholders) -> II. Specification-Driven API Contracts & Validation
  - (template placeholders) -> III. Domain Errors & HTTP Classification
  - (template placeholders) -> IV. External Integrations Are Adapters
  - (template placeholders) -> V. Immutable Project Structure
- Added sections:

  - Authoritative Structure Blueprint
  - Workflow & Quality Gates
- Removed sections:

  - None (template placeholders replaced)
- Templates requiring updates:

  - ✅ updated: .specify/templates/plan-template.md
  - ✅ updated: .specify/templates/spec-template.md
  - ✅ updated: .specify/templates/tasks-template.md
  - ✅ updated: .specify/templates/checklist-template.md
  - ✅ updated: .specify/templates/agent-file-template.md (project name hint)
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
source of truth for API contracts (OpenAPI YAML and central JSON Schemas).

Non-negotiables:
- Any API contract change MUST start by updating `specs/` first.
- All JSON payload validation is the exclusive responsibility of the inbound adapter layer.
- Pydantic models in `src/adapters/inbound/api/schemas/` MUST strictly mirror the schemas and
  OpenAPI definitions under `specs/`.
- Invalid payloads MUST be rejected before reaching core use cases, using:
  - `422 Unprocessable Entity` for schema/validation errors
  - `400 Bad Request` for malformed requests that cannot be interpreted

Rationale: Prevents contract drift and keeps the core free of transport concerns.

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
- Stack traces and internal error details MUST NOT be returned to clients.

Required HTTP classification:
- `400 Bad Request`: Malformed business logic requests.
- `401 Unauthorized`: Failed LDAP authentication.
- `403 Forbidden`: Insufficient LDAP authorization/roles.
- `404 Not Found`: Requested graph nodes/dependencies do not exist in MongoDB.
- `409 Conflict`: State conflicts (e.g., attempting to create a duplicate edge).
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
+-- specs/                  # Specification-First artifacts (OpenAPI YAML, central JSON Schemas).
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
¦   ¦   ¦       +-- schemas/      # Pydantic models mirroring `specs/`.
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

- Specs-first: any API change MUST update `specs/` before code is implemented.
- Architecture boundaries: new business rules MUST go to `src/core/domain/` and/or

  `src/core/use_cases/`; adapters MUST remain thin.
- Ports-first: any new external integration capability MUST be introduced as a port in

  `src/core/ports/` and implemented in an adapter.
- Validation-first (inbound): requests MUST be validated in

  `src/adapters/inbound/api/schemas/` before calling core use cases.
- Error mapping: any new domain exception MUST be mapped in `src/infrastructure/errors/`.
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
  - `specs/` is the source of truth and is updated when contracts change
  - Inbound validation rejects invalid payloads before the core
  - Domain exceptions are mapped to correct HTTP responses
  - Folder structure remains unchanged unless explicitly approved

**Version**: 1.0.0 | **Ratified**: 2026-03-14 | **Last Amended**: 2026-03-14
