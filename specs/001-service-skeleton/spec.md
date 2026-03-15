# Feature Specification: Service Architectural Skeleton

**Feature Branch**: `001-service-skeleton`  
**Created**: 2026-03-14  
**Status**: Draft  
**Input**: User description: "Define the architectural skeleton for the Dependency Graph Service. The goal is to scaffold the directory structure and the foundational wiring of the application. Objectives: Initialize the full directory tree defined in the Constitution. Define the Specification-First workflow (validation models in adapters map to schemas in /specs). Define the Dependency Injection strategy for wiring MongoDB Atlas and LDAP adapters to Core Ports. Establish a global error-handling pattern that maps core exceptions to standardized HTTP responses."

## Constitution Constraints *(mandatory)*

- **Hexagonal Architecture**: Business rules MUST remain isolated in `src/core/` and must not import
  delivery, persistence, or third-party integration libraries.
- **Ports-first**: All communication between core and external systems MUST go through abstract
  port interfaces (ABCs) in `src/core/ports/`.
- **Specs-first**: API contracts and JSON schemas under `specs/` are the single source of truth.
- **Inbound validation**: All request payload validation MUST happen in the inbound adapter layer
  (before invoking core use cases).
- **Error mapping**: Domain exceptions in `src/core/exceptions/` MUST be mapped to correct HTTP
  responses by global handlers in `src/infrastructure/errors/`.
- **Immutable structure**: The baseline folder structure in the constitution MUST NOT be changed.

## Clarifications

### Session 2026-03-14

- Q: What standard error response body format should this service use? → A: RFC 7807 `application/problem+json` (Problem Details) with optional stable `error_code`.
- Q: What lifecycle should Dependency Injection use for MongoDB/LDAP clients and adapters? → A: App-singleton (initialize on startup, reuse per request, close on shutdown).
- Q: Should core ports/use cases be sync or async? → A: Sync core + sync ports (concurrency handled in the inbound adapter layer).
- Q: How should the project enforce the “core purity” rule (core must not import delivery/adapters/drivers)? → A: Automated import-boundary check in CI (fails build on forbidden imports).
- Q: How should inbound payload validation models be kept in sync with the contract schemas (specs-first workflow)? → A: Generate models from schemas, commit generated models, and have CI verify they’re up-to-date.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Scaffold the baseline structure (Priority: P1)

As a developer starting work on the Dependency Graph Service, I need the repository to contain the
full baseline directory structure and the minimal application composition points so that future
features can be implemented without debating layout or layering.

**Why this priority**: Without a stable skeleton, every subsequent feature risks inconsistent
structure and architectural drift.

**Independent Test**: Can be tested by verifying that all baseline directories exist and that the
application entry point can be imported/loaded without pulling infrastructure dependencies into the
core.

**Acceptance Scenarios**:

1. **Given** a clean checkout of the repository, **When** the baseline structure is scaffolded,
   **Then** all directories defined in the constitution exist under `specs/`, `src/`, and `tests/`.
2. **Given** the scaffolded repository, **When** a developer imports the application entry point,
   **Then** core modules (`src/core/**`) can be imported without importing adapter/framework
   libraries.

---

### User Story 2 - Enforce specs-first validation at the boundary (Priority: P2)

As an API consumer (and as a developer maintaining contracts), I need invalid request payloads to be
rejected consistently at the API boundary, based on the schemas in `specs/`, before any business
logic executes.

**Why this priority**: Contract compliance is foundational for correctness and prevents invalid
data from reaching core logic.

**Independent Test**: Can be tested by submitting a request with a schema-violating payload and
verifying a validation response is returned and the core use case is not invoked.

**Acceptance Scenarios**:

1. **Given** an endpoint with a defined JSON schema in `specs/`, **When** a request payload violates
  that schema, **Then** the API responds with `422 Unprocessable Entity` (or `400 Bad Request` if
  the request cannot be interpreted) using Problem Details (`application/problem+json`) and does
  not execute the corresponding core use case.

---

### User Story 3 - Standardize error responses via global handlers (Priority: P3)

As an API consumer, I need business-rule failures to be returned as consistent, semantically
correct HTTP responses without leaking internal stack traces.

**Why this priority**: Predictable errors reduce integration friction and prevent accidental
information disclosure.

**Independent Test**: Can be tested by forcing a core use case to raise known domain exceptions and
verifying the HTTP status code and response body classification.

**Acceptance Scenarios**:

1. **Given** a core use case raises a domain exception, **When** the exception propagates to the
  API layer, **Then** a global handler maps it to the correct HTTP status code per the constitution
  and returns a sanitized RFC 7807 Problem Details response (`application/problem+json`, no stack
  trace).

---

### Edge Cases

- Missing required runtime configuration for external integrations (e.g., connection settings).
- Outbound adapter fails during initialization (e.g., cannot connect) vs during request handling.
- Schema drift between `specs/` and inbound validation models.
- Core raises an unknown/unhandled exception.
- A request is syntactically valid JSON but semantically invalid for the use case.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST contain the full baseline directory tree defined in the
  constitution under `specs/`, `src/`, and `tests/`.
- **FR-002**: The application MUST define a single composition/wiring entry point (the
  application factory) responsible for creating the API application and wiring dependencies.
- **FR-003**: Dependency Injection MUST be explicit and centralized: adapters are instantiated at
  the infrastructure boundary and provided to core use cases via port interfaces (enabling test
  doubles to be swapped in without changing core code).
- **FR-003a**: MongoDB and LDAP clients/adapters MUST use an app-singleton lifecycle: instantiated
  once at application startup, reused per request, and closed on application shutdown.
- **FR-003b**: Core use cases and port interfaces MUST be synchronous (non-async). Any
  concurrency/async execution concerns are handled in the inbound adapter layer without changing
  the core interfaces.
- **FR-004**: Core outbound contracts MUST be expressed as port interfaces (ABCs) in
  `src/core/ports/` for:
  - Persistence of dependency graph data (MongoDB-backed implementation).
  - Authentication and directory lookup (LDAP-backed implementation).
- **FR-005**: Concrete implementations for ports MUST live exclusively in outbound adapters:
  - `src/adapters/outbound/mongodb/` for persistence.
  - `src/adapters/outbound/ldap/` for authentication/lookup.
- **FR-006**: Core business rules MUST be implemented only in `src/core/domain/` and
  `src/core/use_cases/`, and MUST NOT import inbound/outbound adapter code.
- **FR-007**: API payload validation MUST be performed in the inbound adapter layer using models
  located in `src/adapters/inbound/api/schemas/`.
- **FR-008**: Validation models in `src/adapters/inbound/api/schemas/` MUST be traceable to the
  source-of-truth schemas/contracts in `specs/` by maintaining an explicit mapping (e.g., a
  documented reference to the schema file(s) that define each endpoint payload).
- **FR-009**: Invalid payloads MUST be rejected before invoking core use cases using `422` for
  schema/constraint validation failures and `400` for malformed/uninterpretable requests.
- **FR-010**: Domain-specific failures MUST raise custom exceptions in `src/core/exceptions/` and
  MUST NOT include HTTP terminology or status codes.
- **FR-011**: Global exception handlers in `src/infrastructure/errors/` MUST map domain exceptions
  to HTTP status codes per the constitution and MUST prevent stack traces from leaking to clients.
- **FR-012**: All non-2xx API error responses (including validation errors and mapped domain
  exceptions) MUST use RFC 7807 Problem Details (`application/problem+json`) as the default
  representation.
- **FR-013**: Problem Details responses MUST include, at minimum, `type`, `title`, `status`, and
  `detail`; responses MAY include an `error_code` field for stable machine-readable classification
  and MAY include structured validation details as extensions.
- **FR-014**: The implementation MUST include an enforceable import-boundary rule that prevents
  `src/core/` from importing delivery/persistence/integration libraries; this rule MUST run in CI
  and fail the build on violation.
- **FR-015**: Inbound validation models in `src/adapters/inbound/api/schemas/` MUST be generated
  from the source-of-truth contract schemas in `specs/`, committed to the repository, and verified
  in CI as up-to-date with the current schemas.

### Verification Approach

The feature is considered accepted when the user-story scenarios and success criteria provide
coverage for the functional requirements as follows:

- **FR-001**: Verified by User Story 1, Scenario 1 and SC-001.
- **FR-002**: Verified by User Story 1, Scenario 2 (composition point exists and loads cleanly).
- **FR-003 / FR-003a / FR-003b**: Verified by User Story 1, Scenario 2 (core remains decoupled; dependencies wired at the boundary; clients not created per request; core interfaces remain sync).
- **FR-004 / FR-005**: Verified by repository structure review plus User Story 1, Scenario 2 (core imports remain clean).
- **FR-006 / FR-008 / FR-009**: Verified by User Story 2, Scenario 1 and SC-002.
- **FR-010 / FR-011 / FR-012 / FR-013**: Verified by User Story 3, Scenario 1 and SC-003.
- **FR-014**: Verified by SC-004.
- **FR-015**: Verified by a CI check that fails when generated schemas/models are out of date.

### Out of Scope

- Full implementation of dependency graph business operations (create/read/update edges/nodes) not
  required beyond what is necessary to validate the skeleton.
- Production deployment pipeline, monitoring, or full observability stack.

### Assumptions

- The repository will follow the constitution’s mandated technology choices and directory map.
- The service is an HTTP JSON API and will be driven by contracts in `specs/`.

### Dependencies

- Access to MongoDB Atlas and LDAP endpoints (or test doubles) for end-to-end integration testing.
- A repeatable way to validate that schemas in `specs/` and inbound validation models remain aligned.

### Key Entities *(include if feature involves data)*

- **Port**: A core-defined contract (ABC) describing how the core interacts with an external system.
- **Adapter**: A concrete implementation of a port (inbound or outbound).
- **Use Case**: Core orchestration that coordinates domain rules with ports.
- **Domain Exception**: A core exception representing a business-rule failure with contextual data.
- **Contract Schema**: The source-of-truth API contract artifact under `specs/`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of constitution-mandated directories exist after scaffolding and are referenced
  in the repository as the baseline layout.
- **SC-002**: For a representative schema-violating request, the API returns `422` (or `400` when
  uninterpretable) and the corresponding core use case is not executed.
- **SC-003**: For each standardized error category exercised by this skeleton (validation errors
  `400` and `422`, mapped domain errors like `404` and `409`, framework HTTP errors like `404`/`405`,
  and fallback `500`), the API returns the correct HTTP status code and does not include a stack
  trace in the response; the default error response format is RFC 7807 Problem Details
  (`application/problem+json`).
- **SC-004**: The CI architecture boundary check that prevents core importing adapter/framework
  libraries fails reliably if a prohibited import is introduced.
- **SC-005**: Under a representative workload (e.g., multiple sequential requests), MongoDB/LDAP
  clients are not re-instantiated per request (singleton lifecycle).
- **SC-006**: Core port interfaces and use case APIs remain synchronous (no async signatures).
- **SC-007**: A CI check fails if committed inbound validation models are not in sync with `specs/`.
