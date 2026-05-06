# Feature Specification: Micro Affinity Group Submission

**Feature Branch**: `007-add-micro-affinity-endpoint`  
**Created**: 2026-05-05  
**Status**: Draft  
**Input**: User description: "Create a new REST API endpoint to accept and manage JSON documents. Each document represents a micro affinity group object. Endpoint: POST /micro-affinity-groups. Input: JSON document. Validate the incoming document against the sample micro affinity group structure, require every field except name, enforce semantic version and Zulu timestamp metadata formats, verify referenced workloads exist in the matching application architecture document, persist into the micro-affinity-groups collection with overwrite-on-duplicate behavior, and add comprehensive route and validation test coverage."

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

## Clarifications

### Session 2026-05-05

- Q: How should the endpoint handle request fields that are not defined by the sample-derived schema? → A: Reject any field not defined by the sample-derived micro affinity group schema.
- Q: Which exact `effective-date` timestamp format should the endpoint accept? → A: Accept only `YYYY-MM-DDTHH:MM:SSZ`.
- Q: How should the endpoint handle duplicate `workload.id` values within a single request? → A: Reject duplicate `workload.id` values within the same request.
- Q: Can the `workloads` array be empty? → A: Reject requests where `workloads` is empty.
- Q: How should `workload.asset-id` be validated? → A: Require `workload.asset-id` to match the `metadata.asset-id` of the same resolved service node.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit a Valid Micro Affinity Group (Priority: P1)

As a service client, I want to submit a valid micro affinity group document so that the system stores a managed group record tied to the intended architecture version and environment.

**Why this priority**: Accepting and storing a valid document is the core outcome of the feature. Without this flow, the endpoint has no business value.

**Independent Test**: Can be fully tested by submitting a document that matches the defined micro affinity group structure and workload reference rules, then verifying that the service stores the full document and returns a success response.

**Acceptance Scenarios**:

1. **Given** a JSON document that contains all required fields except `name`, uses a valid semantic version in `architecture-version`, uses `effective-date` in `YYYY-MM-DDTHH:MM:SSZ` format, and references workloads that are present in the matching application architecture document, **When** the client submits it to `POST /micro-affinity-groups`, **Then** the service stores the full document in the managed collection and returns a success response.
2. **Given** a valid document that omits `name` but satisfies all other structural and reference rules, **When** the client submits it, **Then** the service accepts the document as valid and stores it successfully.

---

### User Story 2 - Reject Invalid or Unresolvable Documents (Priority: P2)

As a service client, I want invalid micro affinity group documents to be rejected immediately so that only internally consistent records are stored.

**Why this priority**: The endpoint is only trustworthy if it blocks malformed documents, invalid metadata, and workload references that cannot be reconciled to an existing architecture record.

**Independent Test**: Can be fully tested by submitting malformed JSON, structurally invalid documents, and documents whose workload references do not resolve against the matching application architecture, then verifying that nothing is stored.

**Acceptance Scenarios**:

1. **Given** a request body that is malformed JSON or does not follow the defined micro affinity group structure, **When** the client submits it, **Then** the service rejects the request before any persistence occurs.
2. **Given** a document whose `architecture-version` or `effective-date` value does not match the required format, **When** the client submits it, **Then** the service rejects the request and reports the document as invalid.
3. **Given** a document whose `parent-asset-id` and `architecture-version` do not identify a matching application architecture record, **When** the client submits it, **Then** the service rejects the request and does not store the document.
4. **Given** a document whose matching application architecture record exists but does not contain a `service` node with `metadata.code-repo` equal to a submitted `workload.id`, **When** the client submits it, **Then** the service rejects the request and does not store the document.
5. **Given** a document that includes an unexpected top-level field or an unexpected field inside a `workloads` entry, **When** the client submits it, **Then** the service rejects the request and does not store the document.
6. **Given** a document that repeats the same `workload.id` more than once, **When** the client submits it, **Then** the service rejects the request and does not store the document.
7. **Given** a document whose `workloads` array is empty, **When** the client submits it, **Then** the service rejects the request and does not store the document.
8. **Given** a document whose `workload.id` resolves to a `service` node but whose `workload.asset-id` does not equal that node's `metadata.asset-id`, **When** the client submits it, **Then** the service rejects the request and does not store the document.

---

### User Story 3 - Overwrite a Matching Existing Record (Priority: P3)

As a service client, I want repeated submissions for the same micro affinity group identity to overwrite the existing record so that the stored document always reflects the latest accepted payload for that unique key.

**Why this priority**: Deterministic overwrite behavior prevents duplicate managed records and preserves a single current document for each unique identity.

**Independent Test**: Can be fully tested by submitting a valid document, submitting a second valid document with the same `micro-ag-id`, `environment`, and `architecture-version` but different content, and verifying that only one record remains and it matches the second submission.

**Acceptance Scenarios**:

1. **Given** an existing stored document with the same `micro-ag-id`, `environment`, and `architecture-version` as a new valid submission, **When** the client submits the new document, **Then** the service fully replaces the stored record with the new payload and returns the stored replacement document.
2. **Given** an existing stored document with the same `micro-ag-id` but a different `environment` or `architecture-version`, **When** the client submits a new valid document, **Then** the service stores it as a separate record rather than overwriting the existing one.

### Edge Cases

- The request omits `name` while providing all other required fields.
- The request omits a required field such as `micro-ag-id`, `parent-asset-id`, `environment`, `architecture-version`, `effective-date`, or `workloads`.
- The request includes `workloads` but the array is empty.
- `architecture-version` contains `1.0`, `v1.0.0`, `01.2.3`, or any other non-conforming semantic version string.
- `effective-date` appears date-like but is not exactly in `YYYY-MM-DDTHH:MM:SSZ` format.
- `workloads` contains duplicate `id` values.
- A matching application architecture document exists for the requested asset and version, but one submitted workload maps to a node that is not of type `service`.
- A matching application architecture document exists, but one submitted workload `id` has no node with matching `metadata.code-repo`.
- A matching application architecture document exists and a workload `id` resolves to a service node, but the submitted `asset-id` does not match that node's `metadata.asset-id`.
- The same `micro-ag-id` is resubmitted for a different environment and must coexist with the original record.
- The request body is syntactically valid JSON but uses incorrect field types, such as a non-string `effective-date` or a non-array `workloads` value.
- The request includes an unexpected top-level field or an unexpected nested field inside a workload entry.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose `POST /micro-affinity-groups` to accept a single micro affinity group JSON document per request.
- **FR-002**: The request body MUST represent a micro affinity group document using the field structure inferred from `specs/samples/micro-affinity-group/micro-affinity-group.json`.
- **FR-003**: The document MUST support the top-level fields `micro-ag-id`, `name`, `parent-asset-id`, `architecture-version`, `environment`, `effective-date`, and `workloads`.
- **FR-004**: All top-level fields except `name` MUST be required.
- **FR-005**: Each item in `workloads` MUST include `id` and `asset-id`, and MUST NOT include undefined extra fields.
- **FR-006**: `workloads` MUST contain at least one item.
- **FR-007**: `architecture-version` MUST be a string in `major.minor.patch` format with non-negative integers and no leading zeroes except the value `0`.
- **FR-008**: `effective-date` MUST be a string in the exact format `YYYY-MM-DDTHH:MM:SSZ`.
- **FR-009**: The system MUST reject malformed JSON before business validation or persistence begins.
- **FR-010**: The system MUST reject any document whose field types or required field presence do not match the defined micro affinity group request structure.
- **FR-011**: The system MUST reject any top-level or nested request field that is not defined by the sample-derived micro affinity group schema.
- **FR-012**: The system MUST reject a request if the `workloads` array contains duplicate `id` values.
- **FR-013**: For each submitted `workload.id`, the system MUST locate an application architecture document whose `metadata.AssetID` equals the submitted `parent-asset-id` and whose `metadata.version` equals the submitted `architecture-version`.
- **FR-014**: If no application architecture document exists for the submitted `parent-asset-id` and `architecture-version`, the system MUST reject the micro affinity group document.
- **FR-015**: For each submitted `workload.id`, the matching application architecture document MUST contain at least one node whose `node-type` is `service` and whose `metadata.code-repo` equals that `workload.id`.
- **FR-016**: For each submitted workload, the submitted `workload.asset-id` MUST equal the `metadata.asset-id` of the resolved `service` node whose `metadata.code-repo` matches that workload's `id`.
- **FR-017**: If any submitted `workload.id` cannot be matched to a qualifying `service` node in the matching application architecture document, the system MUST reject the micro affinity group document.
- **FR-018**: If any submitted `workload.asset-id` does not match the `metadata.asset-id` of the resolved `service` node, the system MUST reject the micro affinity group document.
- **FR-019**: For valid submissions, the system MUST persist the full JSON document in the `micro-affinity-groups` collection.
- **FR-020**: Stored micro affinity group records MUST be uniquely identified by the exact combination of `micro-ag-id`, `environment`, and `architecture-version`.
- **FR-021**: When a valid submission matches an existing record with the same `micro-ag-id`, `environment`, and `architecture-version`, the system MUST fully overwrite the existing record with the new document.
- **FR-022**: When a valid submission differs from an existing record by either `environment` or `architecture-version`, the system MUST store it as a separate record.
- **FR-023**: A successful submission MUST return the stored document in the response body.
- **FR-024**: When a valid submission creates a new unique record, the system MUST return `201 Created`.
- **FR-025**: When a valid submission overwrites an existing unique record, the system MUST return `200 OK`.
- **FR-026**: Requests rejected for malformed JSON MUST return `400 Bad Request`.
- **FR-027**: Requests rejected for document structure, field format, or workload reference validation failures MUST return `422 Unprocessable Entity`.
- **FR-028**: The feature MUST include automated tests covering successful creation, overwrite behavior, coexistence of records with different unique keys, malformed JSON rejection, field-level validation failures, unknown-field rejection, duplicate-workload rejection, empty-workloads rejection, `workload.asset-id` to resolved-node mismatch rejection, and workload reference validation failures.
- **FR-029**: The feature MUST preserve the current separation of request validation, business rules, persistence logic, and HTTP error mapping within the existing service architecture.

## Assumptions

- Only submission and overwrite behavior for `POST /micro-affinity-groups` is in scope; retrieval, listing, deletion, and partial update behaviors are out of scope.
- The sample document in `specs/samples/micro-affinity-group/micro-affinity-group.json` defines the supported request shape for this feature, and any field not present in that sample is outside the initial scope unless required by existing shared architecture contracts.
- The request contract is closed: fields not present in the sample-derived schema are treated as invalid input rather than pass-through metadata.
- Each `workload.id` is unique within a single submitted document.
- The `workloads` array must contain at least one workload entry.
- A single matching application architecture document is sufficient to validate all submitted workloads for a request, provided it matches the submitted `parent-asset-id` and `architecture-version`.
- For each workload, `asset-id` is validated against the `metadata.asset-id` of the resolved `service` node rather than treated as informational-only input.
- `effective-date` accepts only whole-second UTC timestamps and does not accept fractional seconds or alternate ISO 8601 UTC representations.
- Successful responses return the stored representation of the document so clients can confirm the final persisted payload.

### Key Entities *(include if feature involves data)*

- **Micro Affinity Group Document**: A JSON document that defines a micro affinity group through its identity, optional display name, parent architecture reference, target environment, effective date, and workload list.
- **Micro Affinity Group Workload**: A workload entry inside the document that identifies a code repository plus the expected service-node `metadata.asset-id`, and must resolve to a qualifying service node in the related application architecture.
- **Application Architecture Document**: An existing architecture record identified by asset and version that provides the authoritative source used to validate whether each submitted workload reference is legitimate.
- **Micro Affinity Group Record**: The persisted managed representation of a submitted document, uniquely keyed by `micro-ag-id`, `environment`, and `architecture-version`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, 100% of documents that satisfy the defined request structure, metadata formats, and workload reference rules are accepted and stored successfully.
- **SC-002**: In acceptance testing, 100% of malformed JSON requests and structurally invalid documents are rejected before any record is written or overwritten.
- **SC-003**: In acceptance testing, 100% of submissions containing a workload reference that cannot be matched to a qualifying service node in the corresponding application architecture are rejected without persistence.
- **SC-004**: In acceptance testing, re-submitting the same unique key overwrites the existing record in 100% of cases, while submissions with a different environment or architecture version coexist in 100% of cases.
- **SC-005**: For valid submissions up to 250 KB, at least 95 out of 100 sequential requests complete within 2 seconds as observed by the client in the test environment.
