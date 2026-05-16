# Feature Specification: V1 API Version Prefixing

**Feature Branch**: `009-v1-api-prefixing`  
**Created**: 2026-05-16  
**Status**: Draft  
**Input**: User description: "Implement /v1 API Version Prefixing

Problem Statement:
The FastAPI service currently exposes endpoints directly at the root path (e.g., `/micro-affinity-groups`). To support clean API versioning, all business endpoints must be prefixed with `/v1`.

Requirements:
1. Path Modification:

Add the prefix /v1 to the following API endpoints:
/components/validate
/components
/components/{component_id}
/components/{node_id}/dependencies
/application-architectures
/application-architectures

2. Exclusions:
The infrastructure health check (`GET /health`) and automatic documentation routes (`/docs`, `/redoc`, `/openapi.json`) must remain unversioned at the root path.

3. Preservation of Semantics:
Do not alter Pydantic request/response models, dependency injections (`Depends`), or HTTP status codes.

Out of Scope
- Rewriting individual route function signatures or core business logic."

## Constitution Constraints *(mandatory)*

- **Hexagonal Architecture**: Business rules belong in `src/core/` and must not import framework/driver
  libraries (e.g., `fastapi`, `pymongo`/`motor`, `ldap3`).
- **Specs-first**: Any change to feature intent, behavioral requirements, or software specifications
  MUST start by updating `specs/`.
- **Canonical contracts**: Any change to shared or canonical data contracts MUST start by updating
  `schemas/`.
- **Inbound validation**: All JSON payload validation occurs in the inbound adapter via Pydantic
  schemas in `src/adapters/inbound/api/schemas/` before calling core use cases.
- **Error mapping**: Domain exceptions live in `src/core/exceptions/` and are mapped to HTTP in
  `src/infrastructure/errors/` (no stack traces returned to clients).
- **Immutable structure**: Do not add/remove/rename folders from the baseline structure.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Call Versioned Business Routes (Priority: P1)

As an API consumer, I want the service's business operations to be available under `/v1` so that I can call a stable, explicitly versioned API surface.

**Why this priority**: The main purpose of the feature is to introduce a versioned contract boundary for business-facing operations without changing what those operations do.

**Independent Test**: Can be fully tested by calling each in-scope business operation through its `/v1/...` path and verifying that it accepts the same payloads, returns the same response shapes, and preserves the same success and failure outcomes as before.

**Acceptance Scenarios**:

1. **Given** a client sends a valid request to a moved component route, **When** the client calls the `/v1`-prefixed path, **Then** the service processes the request successfully and returns the same contract and status outcome that the corresponding root-path route previously returned.
2. **Given** a client sends a valid request to an existing application architecture route, **When** the client calls the `/v1/application-architectures` path, **Then** the service processes the request successfully and returns the same contract and status outcome that the corresponding root-path route previously returned.
3. **Given** a client sends a valid request to the existing micro affinity group route, **When** the client calls the `/v1/micro-affinity-groups` path, **Then** the service processes the request successfully and returns the same contract and status outcome that the corresponding root-path route previously returned.
4. **Given** a client calls a versioned business route that includes a path parameter, **When** the request is processed, **Then** the parameter is interpreted the same way it was before the prefix was introduced.

---

### User Story 2 - Preserve Root Infrastructure Access (Priority: P2)

As an operator or integrator, I want the health check and automatic API documentation to stay at the root path so that existing operational checks and discovery links do not break.

**Why this priority**: Operational and documentation endpoints are explicitly excluded from versioning and must remain stable while the business API surface changes.

**Independent Test**: Can be fully tested by requesting `/health`, `/docs`, `/redoc`, and `/openapi.json` after the change and verifying they remain available at their current root-path addresses.

**Acceptance Scenarios**:

1. **Given** the service is running after version prefixing is introduced, **When** an operator requests `GET /health`, **Then** the service returns the health response from the root path.
2. **Given** the service is running after version prefixing is introduced, **When** a user opens `/docs`, `/redoc`, or `/openapi.json`, **Then** the documentation resources remain accessible from the root path.

---

### User Story 3 - Avoid Behavioral Regressions During Path Change (Priority: P3)

As an API consumer, I want the versioning change to alter only route addresses so that existing request formats, response formats, and outcome semantics stay consistent.

**Why this priority**: The value of the change is organizational, not behavioral; consumers should only need to update the route prefix, not rework business interactions.

**Independent Test**: Can be fully tested by comparing representative success and error cases before and after the path change and verifying that only the address changes for the moved routes.

**Acceptance Scenarios**:

1. **Given** a moved business route currently returns a defined success status for a valid request, **When** the same request is sent to the `/v1`-prefixed route, **Then** the route returns the same success status and response shape.
2. **Given** a moved business route currently returns a defined client or server error for an invalid or failing request, **When** the same request is sent to the `/v1`-prefixed route, **Then** the route returns the same error status and response shape.

### Edge Cases

- A client continues to call a moved business route at its former root-path address after `/v1` becomes the supported route prefix.
- A route with path parameters, such as component lookup or dependency lookup, is called through `/v1` and must preserve current identifier matching behavior.
- A business route that accepts complex request payloads, such as `/micro-affinity-groups`, is moved under `/v1` and must preserve the same validation and persistence outcomes.
- Root-path documentation remains available while describing business routes under their new `/v1/...` addresses.
- Health checks remain available at `/health` even though business routes are versioned.
- The service exposes versioned business routes without creating ambiguous duplicates for the same supported operation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose the current `POST /components/validate` business operation at `POST /v1/components/validate`.
- **FR-002**: The system MUST expose the current business operations mounted at `/components` at `/v1/components`, including create-or-update behavior and component retrieval by identifier.
- **FR-003**: The system MUST expose the current dependency lookup operation mounted at `/components/{node_id}/dependencies` at `/v1/components/{node_id}/dependencies`.
- **FR-004**: The system MUST expose all current business operations mounted at `/application-architectures` at `/v1/application-architectures`.
- **FR-005**: The system MUST expose the current business operations mounted at `/micro-affinity-groups` at `/v1/micro-affinity-groups`.
- **FR-006**: Every business operation moved under `/v1` MUST preserve its current HTTP method, request body contract, response body contract, path parameter meaning, and success and error status codes.
- **FR-007**: The introduction of the `/v1` prefix MUST NOT change the business rules executed by the moved operations.
- **FR-008**: The introduction of the `/v1` prefix MUST NOT change the request-processing dependencies or route-specific prerequisites currently applied to the moved operations.
- **FR-009**: `GET /health` MUST remain available at the root path and MUST NOT require a `/v1` prefix.
- **FR-010**: `/docs`, `/redoc`, and `/openapi.json` MUST remain available at the root path and MUST NOT require a `/v1` prefix.
- **FR-011**: The root-path API documentation resources MUST describe the moved business operations using their `/v1/...` addresses.
- **FR-012**: The former root-path addresses for business operations moved under `/v1` MUST no longer remain active as the supported business routes after this feature is released.
- **FR-013**: The feature MUST include automated tests covering each moved business route at its `/v1` address, including `/v1/micro-affinity-groups`, the continued root-path availability of `GET /health`, and the continued root-path availability of `/docs`, `/redoc`, and `/openapi.json`.

## Assumptions

- The duplicate `/application-architectures` entry in the request refers to the existing route group at that path rather than two different paths.
- This feature changes route addresses only; it does not introduce a new API version selection mechanism, change payload content, or alter business rules.
- Root-path business routes that move under `/v1` are replaced by their versioned equivalents rather than being kept as long-term duplicate supported routes.
- The current scope includes the listed route groups plus the existing `/micro-affinity-groups` business endpoint, based on clarification that it should also move under `/v1`.

### Key Entities *(include if feature involves data)*

- **Versioned Business Route**: A client-facing business operation whose supported address includes the `/v1` prefix while preserving the existing behavior of that operation.
- **Root Infrastructure Route**: An operational or discovery route that remains available without versioning, specifically the health check and automatic documentation resources.
- **API Consumer Request**: A client request sent to a business route, including its method, path, path parameters, request body, and expected success or failure outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, 100% of the in-scope business operations, including `/v1/components/validate`, `/v1/components`, `/v1/components/{component_id}`, `/v1/components/{node_id}/dependencies`, `/v1/application-architectures`, and `/v1/micro-affinity-groups`, are reachable through `/v1` and return the same request and response contracts and the same status outcomes as before the prefix was introduced.
- **SC-002**: In acceptance testing, 100% of checks to `GET /health`, `/docs`, `/redoc`, and `/openapi.json` continue to succeed from their root-path addresses after the versioning change.
- **SC-003**: In documentation verification, the published API description at the root path lists the moved business operations under `/v1/...` and does not present the former root-path addresses as supported business routes.
- **SC-004**: In automated regression coverage, every moved business route, including `/v1/micro-affinity-groups`, has at least one success-path verification and the root infrastructure routes each have at least one availability verification.
