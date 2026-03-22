# Feature Specification: Components Echo Endpoint

**Feature Branch**: `[002-components-echo]`  
**Created**: 2026-03-19  
**Status**: Draft  
**Input**: User description: "Add an endpoint named components that takes an arbitrary JSON as input and prints it out."

## Clarifications

### Session 2026-03-19

- Q: How should the service "print it out" (log) arbitrary JSON payloads? → A: Log the JSON payload at INFO, truncating the logged representation to the first 4096 characters and indicating truncation.


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

### User Story 1 - Echo any JSON payload (Priority: P1)

As an API client, I want to POST any valid JSON to the `/components` endpoint and receive the exact same JSON back so I can quickly verify connectivity, request formatting, and server behavior.

**Why this priority**: This is the core feature value: a simple round-trip echo that confirms the service can accept and return arbitrary JSON.

**Independent Test**: Can be fully tested by sending a JSON payload to `POST /components` and verifying a `200 OK` response whose JSON body matches the request payload.

**Acceptance Scenarios**:

1. **Given** the service is running, **When** a client sends `POST /components` with a valid JSON object body, **Then** the response is `200 OK`, the response body equals the request body, and the received payload is recorded in application logs (truncated with truncation indicated when the logged representation would exceed 4096 characters).
2. **Given** the service is running, **When** a client sends `POST /components` with a valid JSON body that is not an object (e.g., array, string, number, boolean, or null), **Then** the response is `200 OK`, the response body equals the request body, and the received payload is recorded in application logs (truncated with truncation indicated when the logged representation would exceed 4096 characters).

---

### User Story 2 - Invalid JSON returns a clear error (Priority: P2)

As an API client, I want to receive a consistent, structured error when I send malformed JSON so I can fix my request without guessing.

**Why this priority**: It protects clients from ambiguous failures and keeps error responses consistent across the API.

**Independent Test**: Can be fully tested by sending an invalid JSON body to `POST /components` and asserting the response is a `400` problem-details payload.

**Acceptance Scenarios**:

1. **Given** the service is running, **When** a client sends `POST /components` with a malformed JSON body, **Then** the response is `400` and the response content type is the standard problem-details media type.

---

### Edge Cases

- Request body is empty or missing.
- Request body is valid JSON but not an object (array, string, number, boolean, null).
- Client sends a non-JSON content type with an invalid or non-JSON body.
- Payload contains deeply nested structures.
- Payload is very large and triggers log truncation.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: System MUST expose an HTTP endpoint `POST /components`.
- **FR-002**: `POST /components` MUST accept any valid JSON value as the request body (object, array, string, number, boolean, or null).
- **FR-003**: For any valid JSON request body, the system MUST respond with `200 OK` and a JSON response body that is exactly equal (structurally and by value) to the request JSON.
- **FR-004**: For any valid JSON request body, the system MUST record the received payload in application logs exactly once per request, truncating the logged representation to the first 4096 characters and indicating when truncation occurs.
- **FR-005**: If the request body is not valid JSON, the system MUST respond with `400` and a problem-details response consistent with the service’s existing error format.
- **FR-006**: The API contract documentation MUST be updated to describe `POST /components`, including that both request and response bodies are free-form JSON.
- **FR-007**: Automated tests MUST cover (at minimum) a JSON object payload, a JSON array payload, and a malformed JSON payload.
- **FR-008**: If the request body is missing, the system MUST respond with `422` and a problem-details response consistent with the service’s existing validation error format.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: For 100% of valid JSON requests, clients receive a `200 OK` response whose JSON body equals the submitted JSON.
- **SC-002**: For 100% of malformed JSON requests, clients receive a `400` response in the service’s standard problem-details format.
- **SC-003**: A reader of the API documentation can correctly identify that `POST /components` accepts and returns free-form JSON without additional guidance.
- **SC-004**: The automated test suite includes coverage for the primary echo flow and the malformed JSON failure mode.

## Assumptions

- The new `POST /components` endpoint is additive and does not change existing `/components/{component_id}` or `/components/validate` behaviors.
- No persistence or domain behavior is introduced; the payload is used only for logging and response echo.
- The service’s existing problem-details mechanism is used for malformed JSON responses.
- The feature relies on the service’s existing validation and error-to-problem-details mapping behavior.
- Clients should not send secrets/PII to POST /components; the service logs the received JSON payload at INFO (truncated) as part of this feature.
