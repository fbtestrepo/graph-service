# Feature Specification: CALM Architecture Document Ingestion

**Feature Branch**: `006-calm-architecture-ingest`  
**Created**: 2026-05-02  
**Status**: Draft  
**Input**: User description: "Create a submission flow for CALM architecture documents that enforces the pinned local contract, requires strict root metadata validation, stores each asset-version pair as a managed architecture record, overwrites repeated submissions for the same asset-version pair, and includes automated coverage for successful and invalid submissions."

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

### Session 2026-05-02

- Q: Which CALM schema file is the authoritative request entry contract for this endpoint? → A: Use `schemas/calm/v1_2/calm.json` as the single authoritative request entry schema.
- Q: How should successful submissions distinguish create vs overwrite outcomes? → A: Return `201 Created` for a new `AssetID + version` record and `200 OK` for an overwrite, with the stored document in both responses.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Submit a Valid CALM Document (Priority: P1)

As an architecture publisher, I want to submit a CALM document to the service so that a validated architecture record is stored and made available for downstream use.

**Why this priority**: Accepting a valid architecture document is the core business outcome. Without this flow, the feature has no value.

**Independent Test**: Can be fully tested by submitting a CALM-compliant document with the required metadata and verifying that the service accepts it, stores the full payload, and returns a success response.

**Acceptance Scenarios**:

1. **Given** a CALM document that conforms to the authoritative request schema in `schemas/calm/v1_2/calm.json` and includes valid `metadata.AssetID`, `metadata.version`, and `metadata.created` values, **When** the client submits it to `POST /application-architectures`, **Then** the service stores the full document and returns a success response.
2. **Given** a CALM document whose `metadata.AssetID` is new and whose `metadata.version` has not been stored for that asset before, **When** the client submits it, **Then** the service creates a new stored architecture record for that exact asset-version combination and returns `201 Created` with the stored document.

---

### User Story 2 - Reject Invalid Architecture Documents (Priority: P2)

As an architecture publisher, I want invalid CALM documents to be rejected immediately so that the repository only contains documents that satisfy the published contract.

**Why this priority**: Contract integrity is essential because downstream consumers cannot rely on stored architecture documents if invalid content can be persisted.

**Independent Test**: Can be fully tested by submitting documents that violate the CALM schema or metadata rules and verifying that the service rejects them without storing any record.

**Acceptance Scenarios**:

1. **Given** a request body that does not conform to the authoritative request schema in `schemas/calm/v1_2/calm.json`, **When** the client submits it, **Then** the service rejects the request and does not store the document.
2. **Given** a request body that omits the root `metadata` object or any required metadata key, **When** the client submits it, **Then** the service rejects the request and identifies the request as invalid.
3. **Given** a request body whose `metadata.AssetID`, `metadata.version`, or `metadata.created` value fails the required format rules, **When** the client submits it, **Then** the service rejects the request and does not alter stored data.

---

### User Story 3 - Overwrite an Existing Architecture Version (Priority: P3)

As an architecture publisher, I want a repeated submission for the same asset and version to replace the previous stored document so that the latest approved content becomes the single source for that asset-version pair.

**Why this priority**: Managing duplicate submissions by deterministic overwrite prevents ambiguity and keeps versioned architecture records stable.

**Independent Test**: Can be fully tested by submitting a valid document for an asset-version pair, submitting a second valid document with the same asset-version pair but different content, and verifying that only one stored record remains and it matches the second submission.

**Acceptance Scenarios**:

1. **Given** an existing stored architecture document for `metadata.AssetID = X` and `metadata.version = Y`, **When** the client submits a new valid document with the same `X` and `Y`, **Then** the service fully overwrites the stored record with the new document and returns `200 OK` with the stored document.
2. **Given** stored architecture documents exist for `metadata.AssetID = X` at version `Y`, **When** the client submits a valid document for the same asset `X` with a different version `Z`, **Then** the service stores it as a separate record rather than overwriting version `Y`.

### Edge Cases

- Request body is valid JSON but omits the root `metadata` object.
- Request body contains `metadata` but is missing one or more required keys: `AssetID`, `version`, or `created`.
- `metadata.AssetID` contains whitespace, punctuation, or other non-alphanumeric characters.
- `metadata.version` contains an invalid semantic version string such as `1.0`, `v1.0.0`, or `01.2.3`.
- `metadata.created` matches the text pattern `YYYY-MM-DD` but is not a valid calendar date.
- Request body satisfies the root metadata rules but fails other CALM schema requirements inherited through `schemas/calm/v1_2/calm.json`.
- A duplicate submission uses the same `AssetID` and `version` but changes non-metadata content elsewhere in the document.
- Two submissions use the same `AssetID` with different `version` values and must coexist.
- Malformed JSON is submitted and cannot be interpreted as a request document.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose `POST /application-architectures` to accept CALM architecture documents.
- **FR-002**: The request body for `POST /application-architectures` MUST be a JSON document that conforms to the authoritative request schema `schemas/calm/v1_2/calm.json`.
- **FR-003**: The service MUST treat `schemas/calm/v1_2/calm.json` as the single authoritative entry contract for request validation, including any referenced CALM sub-schemas.
- **FR-004**: The submitted document MUST contain a root-level `metadata` object.
- **FR-005**: The `metadata` object MUST contain all of the following required keys: `AssetID`, `version`, and `created`.
- **FR-006**: `metadata.AssetID` MUST be a non-empty string containing only ASCII letters and digits.
- **FR-007**: `metadata.version` MUST be a string representing a three-part semantic version in the form `major.minor.patch`, where each part is a non-negative integer and leading zeroes are not allowed except for the value `0`.
- **FR-008**: `metadata.created` MUST be a string representing a valid calendar date in `YYYY-MM-DD` format.
- **FR-009**: The service MUST reject malformed JSON before any domain or persistence processing occurs.
- **FR-010**: The service MUST reject any document that fails the CALM schema rules or the required metadata rules before persisting any data.
- **FR-011**: For valid submissions, the service MUST persist the full JSON document without dropping supported fields.
- **FR-012**: Persisted documents MUST be stored in the `application-architectures` collection.
- **FR-013**: Each stored document MUST be uniquely identified by the exact combination of `metadata.AssetID` and `metadata.version`.
- **FR-014**: When a valid submission matches an existing record with the same `metadata.AssetID` and `metadata.version`, the service MUST fully overwrite the previous stored document with the new submission.
- **FR-015**: When a valid submission has the same `metadata.AssetID` as an existing record but a different `metadata.version`, the service MUST store it as a separate record.
- **FR-016**: When a valid submission creates a new `AssetID + version` record, the service MUST return `201 Created`.
- **FR-017**: When a valid submission overwrites an existing `AssetID + version` record, the service MUST return `200 OK`.
- **FR-018**: A successful submission MUST return the stored architecture document in the response body.
- **FR-019**: Invalid requests caused by malformed JSON MUST produce `400 Bad Request`.
- **FR-020**: Invalid requests caused by schema or metadata validation failures MUST produce `422 Unprocessable Entity`.
- **FR-021**: The feature MUST include automated tests covering successful creation, overwrite of an existing asset-version pair, coexistence of multiple versions for one asset, malformed JSON rejection, and metadata/schema validation failures.
- **FR-022**: The feature MUST preserve the existing modular architectural boundaries by keeping request validation, business rules, and persistence concerns in their respective layers.

## Assumptions

- Only the ingestion endpoint `POST /application-architectures` is in scope for this feature; listing, retrieval, deletion, and search capabilities are out of scope.
- The CALM schema version in scope for this feature is the pinned local schema set in `schemas/calm/v1_2/`, with `schemas/calm/v1_2/calm.json` as the authoritative request entry schema.
- Successful responses return the persisted document after storage so clients can confirm the stored representation.
- The endpoint uses HTTP status codes rather than an extra response flag to distinguish create versus overwrite outcomes.

### Key Entities *(include if feature involves data)*

- **Application Architecture Document**: A submitted CALM JSON document representing an architecture model, including the full domain content plus required root metadata.
- **Architecture Metadata**: The required root metadata object containing `AssetID`, `version`, and `created`, used to validate identity and versioning rules.
- **Architecture Record**: The persisted representation of an Application Architecture Document, uniquely keyed by the combination of `AssetID` and `version`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, 100% of CALM documents that conform to the pinned local schema and required metadata rules are accepted and stored successfully.
- **SC-002**: In acceptance testing, 100% of submissions missing the root `metadata` object, missing required metadata keys, or containing invalid `AssetID`, `version`, or `created` values are rejected before any record is written or overwritten.
- **SC-003**: In acceptance testing, re-submitting a document with the same `AssetID` and `version` overwrites the prior stored record in 100% of cases, and storing a different `version` for the same `AssetID` preserves both records in 100% of cases.
- **SC-004**: For valid submissions up to 1 MB, at least 95 out of 100 sequential requests complete within 2 seconds as observed by the client in the test environment.
