# Feature Specification: Components Payload Validation Schema

**Feature Branch**: `004-components-payload-schema`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Create schema for components endpoint input validation based on the sample json document located in specs/sample-component-payload/sample-mag.json. The node-id field is what uniquely identifies the object represented by the json document. Attributes node-id, node-type, node-name and metadata.parent-asset-id are required. Elements interfaces and relationships are optional. return  400 Bad Request if required fields are missing and a 201/200 for the upsert logic."

## Clarifications

### Session 2026-03-24

- Q: What HTTP status code should be used for schema/constraint validation failures on `POST /components`? → A: Use `422 Unprocessable Entity` for schema/constraint validation failures (missing required fields, unknown fields, wrong types) and reserve `400 Bad Request` for malformed/unparseable JSON.
- Q: Should unknown fields be rejected only at the top-level or also within nested objects? → A: Reject unknown fields at every object level (top-level, `interfaces[]` entries, `relationships[]` entries, and `source`/`target`), except allow extra keys under `metadata`.
- Q: Which MongoDB collection should store the upserted component-node payloads? → A: Upsert into the `components` collection, keyed by `node-id`.
- Q: How should `GET /components/{component_id}` behave given `POST /components` will upsert component-node payloads into the `components` collection keyed by `node-id`? → A: Change `GET /components/{component_id}` to treat the path parameter as the `node-id` value and return the stored component-node payload shape (i.e., the same JSON shape accepted by `POST /components`).

## Constitution Constraints *(mandatory)*

- **Hexagonal Architecture**: Business rules belong in `src/core/` and must not import framework/driver
  libraries (e.g., `fastapi`, `pymongo`/`motor`, `ldap3`).
- **Specs-first**: Any API contract change MUST start by updating `specs/` (OpenAPI + JSON Schemas).
- **Inbound validation**: All JSON payload validation occurs in the inbound adapter via Pydantic
  schemas in `src/adapters/inbound/api/schemas/` before calling core use cases.
- **Error mapping**: Domain exceptions live in `src/core/exceptions/` and are mapped to HTTP in
  `src/infrastructure/errors/` (no stack traces returned to clients).
- **Immutable structure**: Do not add/remove/rename folders from the baseline structure.

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

### User Story 1 - Upsert a Component (Priority: P1)

**As a** client of the service, **I want** to submit a valid component payload to `POST /components`, **so that** the component is created or updated based on its unique `node-id`.

**Why this priority**: This is the primary purpose of the endpoint: accepting component data and performing an upsert keyed by `node-id`.

**Independent Test**: Can be fully tested by sending a valid JSON body (using the sample payload as a baseline) and observing `201` on first submit and `200` on subsequent submits with the same `node-id`.

**Acceptance Scenarios**:

1. **Given** no existing component with `node-id = X`, **When** the client `POST`s a valid payload with `node-id = X`, **Then** the service returns `201 Created`.
2. **Given** an existing component with `node-id = X`, **When** the client `POST`s a valid payload with `node-id = X`, **Then** the service returns `200 OK`.
3. **Given** a valid payload that includes `interfaces` and `relationships`, **When** the client `POST`s to `/components`, **Then** the service returns `200 OK` or `201 Created` (based on whether `node-id` already exists).
4. **Given** an existing component with `node-id = X`, **When** the client `GET`s `/components/X`, **Then** the service returns `200 OK` with the stored component-node payload.

---

### User Story 2 - Reject Invalid Payloads (Priority: P2)

**As a** client of the service, **I want** invalid component payloads to be rejected with a clear client error, **so that** I can fix request data before retrying.

**Why this priority**: Without strict validation, downstream behavior becomes unpredictable and invalid data can leak into storage/graph logic.

**Independent Test**: Can be fully tested by omitting each required field (one at a time) and verifying the response is `422 Unprocessable Entity`.

**Acceptance Scenarios**:

1. **Given** a request body missing `node-id`, **When** the client `POST`s to `/components`, **Then** the service returns `422 Unprocessable Entity`.
2. **Given** a request body missing `metadata.parent-asset-id`, **When** the client `POST`s to `/components`, **Then** the service returns `422 Unprocessable Entity`.
3. **Given** a request body containing an unknown top-level field, **When** the client `POST`s to `/components`, **Then** the service returns `422 Unprocessable Entity`.
4. **Given** a request body containing `relationaships` (misspelled) instead of `relationships`, **When** the client `POST`s to `/components`, **Then** the service returns `422 Unprocessable Entity`.
5. **Given** a request body where an entry in `interfaces` is missing `interface-local-id` or `interface-type`, **When** the client `POST`s to `/components`, **Then** the service returns `422 Unprocessable Entity`.
6. **Given** a request body that is not valid JSON, **When** the client `POST`s to `/components`, **Then** the service returns `400 Bad Request`.

---

### User Story 3 - Allow Minimal Payloads (Priority: P3)

**As a** client of the service, **I want** to omit optional `interfaces` and `relationships`, **so that** I can upsert the minimal required data when additional detail is not available.

**Why this priority**: Allows incremental adoption and partial data availability without blocking writes.

**Independent Test**: Can be fully tested by sending a payload containing only required fields and observing a successful upsert response.

**Acceptance Scenarios**:

1. **Given** a payload containing only required fields, **When** the client `POST`s to `/components`, **Then** the service returns `200 OK` or `201 Created` (depending on whether the `node-id` already exists).

---

### Edge Cases

- Request body is valid JSON but the root value is not an object (e.g., array/string/number)
- `node-id`, `node-type`, or `node-name` is present but is empty or only whitespace
- `metadata` is missing, not an object, or `metadata.parent-asset-id` is missing/empty
- `interfaces` is present but is not an array
- An `interfaces` entry is missing `interface-local-id` or `interface-type`
- `relationships` is present but is not an array
- A `relationships` entry is missing `relationship-type`, `source`, or `target`
- `source`/`target` is missing `node-id` or `interface-local-id`
- Request includes unknown top-level fields
- Request includes `relationaships` (misspelled) instead of `relationships`

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `/components` endpoint MUST accept a JSON request body whose root value is an object.
- **FR-002**: The request body MUST contain the following required fields as non-empty strings:
  - `node-id`
  - `node-type`
  - `node-name`
  - `metadata.parent-asset-id`
- **FR-003**: `node-id` MUST uniquely identify the component for the purpose of upsert behavior.
- **FR-004**: `interfaces` MUST be optional. If present, it MUST be an array of objects where each entry contains:
  - `interface-local-id` (non-empty string)
  - `interface-type` (non-empty string)
- **FR-005**: `relationships` MUST be optional. If present, it MUST be an array of objects where each entry contains:
  - `relationship-type` (non-empty string)
  - `source` object containing `node-id` and `interface-local-id` (both non-empty strings)
  - `target` object containing `node-id` and `interface-local-id` (both non-empty strings)
- **FR-006**: If the request body is not valid JSON, the service MUST return `400 Bad Request`.
- **FR-007**: If any required field is missing or fails validation, the service MUST return `422 Unprocessable Entity`.
- **FR-008**: For a valid request, the service MUST upsert the component keyed by `node-id` and return:
  - `201 Created` when the `node-id` did not previously exist
  - `200 OK` when the `node-id` already existed
- **FR-009**: For `200` and `201` responses, the service MUST return a response body representing the accepted component payload.
- **FR-010**: The service MUST accept requests that include only the required fields (i.e., both `interfaces` and `relationships` omitted).
- **FR-011**: The request body MUST NOT include unknown top-level fields (i.e., only `node-id`, `node-type`, `node-name`, `metadata`, `interfaces`, and `relationships` are allowed).
- **FR-012**: Nested objects MUST NOT include unknown fields:
  - `interfaces[]` entries MUST contain only `interface-local-id` and `interface-type`
  - `relationships[]` entries MUST contain only `relationship-type`, `source`, and `target`
  - `source` and `target` MUST contain only `node-id` and `interface-local-id`
- **FR-013**: The misspelled top-level field `relationaships` MUST be treated as an unknown field and rejected with `422 Unprocessable Entity`.
- **FR-014**: On successful upsert, the service MUST persist the component-node payload to MongoDB in the `components` collection, using `node-id` as the lookup key.
- **FR-015**: `GET /components/{component_id}` MUST retrieve a component by matching `{component_id}` to the stored document's `node-id` and MUST return the stored component-node payload as the response body.
- **FR-016**: If `GET /components/{component_id}` does not find a stored document with `node-id = {component_id}`, the service MUST return `404 Not Found`.

### Assumptions

- Additional keys may appear under `metadata` beyond `parent-asset-id`.

### Out of Scope

- Authentication/authorization behavior changes
- Changes to endpoints other than `POST /components` and `GET /components/{component_id}`
- Accepting misspelled field names (e.g., `relationaships`) as aliases
- Partial updates/patch semantics (each accepted request represents a complete component payload)

### Key Entities *(include if feature involves data)*

- **Component Node**: A component identified by `node-id` with `node-type`, `node-name`, and `metadata` (including `parent-asset-id`).
- **Interface**: A named interface on a component node, identified by `interface-local-id` and classified by `interface-type`.
- **Relationship**: A directed relationship from a source interface to a target interface with a `relationship-type`.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: After a warm-up of 5 valid requests (not counted), in a local test run of 100 sequential valid requests to POST /components, at least 95 requests return (200 or 201) within 1.0s measured as client-observed wall-clock latency (request start → full response received).
- **SC-002**: Submitting a payload missing any required field returns `422 Unprocessable Entity` in 100% of attempts.
- **SC-003**: Re-submitting the same valid payload twice yields `201` on first submit (new `node-id`) and `200` on the second submit (existing `node-id`).
- **SC-004**: A payload containing only required fields (no `interfaces` and no `relationships`) can be successfully upserted.
