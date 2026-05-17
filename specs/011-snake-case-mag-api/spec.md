# Feature Specification: Snake Case MAG API

**Feature Branch**: `011-snake-case-mag-api`  
**Created**: 2026-05-16  
**Status**: Draft  
**Input**: User description: "Update API endpoint /v1/micro-affinity-groups and the associated Pydantic Models to Snake Case

Problem Statement
The current implementation of the endpoint receives JSON payloads and persists documents to MongoDB using keys containing dashes (`kebab-case`). This requires Pydantic alias mapping, creates friction in Python dot-notation, and violates `snake_case` backend standards.

Requirements
1. Update the below sample documents to use `snake_case` for the JSON keys
spec/samples/micro-affinity-group/micro-affinity-group.json
spec/samples/micro-affinity-group/micro-affinity-group-relationships.json

These documents are used for the generation of the input and and output Pydantic models.

2. Model Refactoring: Update all Pydantic models (for both the original and enriched documents) to use `snake_case` fields natively. Remove any `Field(alias="...")` or alias generators that map to `kebab-case`.
  - Example: `"workload-id"` must become `"workload_id"` in the incoming JSON, the Python model, and the MongoDB document.
3. API Contract Update: The REST endpoint must now expect incoming JSON payloads to use `snake_case` keys and will return `snake_case` in its JSON responses.
4. Persistence Alignment: Ensure the MongoDB insertion logic persists both the original and modified documents using the new `snake_case` keys.

Out of Scope
- Modifying the core business logic that enriches the document.
- Writing data migration scripts for historical documents already in MongoDB (this handles new incoming data only)."

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
### User Story 1 - Submit Snake Case Requests (Priority: P1)

As an API client, I want `/v1/micro-affinity-groups` to accept snake_case request bodies so that I can send documents that match Python-oriented backend standards without relying on alias translation.

**Why this priority**: The primary feature value is changing the public contract for incoming submissions so new requests align with the required naming convention.

**Independent Test**: Can be fully tested by submitting a valid snake_case request body to `/v1/micro-affinity-groups` and confirming the request succeeds without requiring kebab-case keys.

**Acceptance Scenarios**:

1. **Given** a client sends a valid micro affinity group request using documented snake_case keys, **When** the request reaches `/v1/micro-affinity-groups`, **Then** the service accepts it and processes it successfully.
2. **Given** a client sends a request using legacy kebab-case keys that were formerly translated by aliases, **When** the request reaches `/v1/micro-affinity-groups`, **Then** the request is rejected as no longer matching the documented contract.

---

### User Story 2 - Receive Snake Case Responses (Priority: P2)

As an API client, I want the endpoint response payloads to use snake_case keys so that request and response documents follow one consistent convention.

**Why this priority**: Once requests move to snake_case, responses must match or clients still need mixed-case handling.

**Independent Test**: Can be fully tested by posting a valid snake_case request and confirming that the response body uses snake_case keys only.

**Acceptance Scenarios**:

1. **Given** a successful micro affinity group submission, **When** the service returns the enriched response, **Then** every documented response key is returned in snake_case.
2. **Given** the canonical sample documents define the input and enriched output contracts, **When** those samples are reviewed after the change, **Then** both documents contain snake_case keys only.

---

### User Story 3 - Persist Snake Case Documents (Priority: P3)

As a service owner, I want newly persisted raw and enriched micro affinity group documents to use snake_case keys so that stored data aligns with the updated API contract and backend naming standards.

**Why this priority**: Persistence must remain aligned with the revised contract; otherwise the API and stored documents would diverge immediately.

**Independent Test**: Can be fully tested by submitting a valid snake_case request and verifying that the newly stored raw and enriched MongoDB documents use snake_case keys while enrichment behavior remains unchanged.

**Acceptance Scenarios**:

1. **Given** a successful submission creates or updates the raw and enriched documents, **When** the stored records are inspected, **Then** both documents use snake_case keys for newly written data.
2. **Given** the feature changes contract shape but not enrichment behavior, **When** a request is processed, **Then** the same business enrichment result is produced with only the key naming convention changed.

### Edge Cases

- Requests that mix snake_case and legacy kebab-case keys must not be treated as valid snake_case submissions.
- Optional fields that were previously accepted via alias mapping, such as workload identifiers and enriched relationship fields, must still behave correctly when supplied only in snake_case.
- Existing historical MongoDB documents that still use kebab-case remain out of scope; the feature applies only to newly written data.
- Sample documents used for model generation must stay synchronized so input and enriched output contracts do not drift apart.
- Error responses for invalid requests must continue using the existing error-handling behavior even though the accepted payload naming convention changes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The canonical sample documents for the micro affinity group input and enriched output contracts MUST use snake_case keys only.
- **FR-002**: `/v1/micro-affinity-groups` MUST accept incoming JSON payloads only when they use the documented snake_case keys.
- **FR-003**: `/v1/micro-affinity-groups` MUST return successful JSON responses using snake_case keys only.
- **FR-004**: Newly persisted raw micro affinity group documents created by this endpoint MUST use snake_case keys.
- **FR-005**: Newly persisted enriched micro affinity group documents created by this endpoint MUST use snake_case keys.
- **FR-006**: The feature MUST remove reliance on kebab-case alias translation for the micro affinity group request and response contract.
- **FR-007**: Fields previously represented with dashes, such as `workload-id`, MUST be represented as their snake_case equivalents everywhere this feature updates the contract.
- **FR-008**: Existing business enrichment behavior for the endpoint MUST remain unchanged aside from key naming.
- **FR-009**: Existing error-handling semantics and status codes for the endpoint MUST remain unchanged aside from validation now expecting snake_case request keys.
- **FR-010**: Historical MongoDB documents that were previously stored using kebab-case keys MUST remain out of scope for migration.
- **FR-011**: The feature MUST update the generated request and response Pydantic contract models used by the endpoint in `src/adapters/inbound/api/schemas/` so that snake_case is their native field naming convention.
- **FR-012**: The feature MUST include automated regression coverage proving that snake_case requests, snake_case responses, and snake_case persistence all operate correctly for newly processed documents.

## Assumptions

- The sample input and enriched output documents referenced by the user are the authoritative source for the endpoint contract updates in this feature.
- The MAG request and response JSON Schemas under `specs/001-service-skeleton/contracts/` are service-local endpoint contract sources for generated Pydantic models in this repository. They are not shared canonical schemas governed under the root `schemas/` directory.
- Only `/v1/micro-affinity-groups` and its directly associated contract models and persistence outputs are in scope; other endpoints remain unchanged.
- Existing persisted documents that still use kebab-case are allowed to remain in storage because historical migration is explicitly out of scope.

### Key Entities *(include if feature involves data)*

- **Micro Affinity Group Submission**: The client-supplied document posted to `/v1/micro-affinity-groups`, including snake_case identifiers, workload information, and effective-date metadata.
- **Enriched Micro Affinity Group Document**: The successful response and persisted enriched document that adds relationship data while following the same snake_case convention.
- **Contract Sample Document**: The canonical sample input or output document used as the source of truth for generated endpoint models.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of documented request and response keys for `/v1/micro-affinity-groups` are snake_case after the change.
- **SC-002**: 100% of successful endpoint responses for newly submitted micro affinity groups return snake_case keys only.
- **SC-003**: 100% of newly persisted raw and enriched micro affinity group documents created during regression testing use snake_case keys only.
- **SC-004**: The full functional regression suite continues to pass without requiring changes to unrelated endpoints or enrichment business rules.
