# Feature Specification: MAG Upsert Uniqueness

**Feature Branch**: `012-mag-upsert-uniqueness`  
**Created**: 2026-05-17  
**Status**: Draft  
**Input**: User description: "Refactor Micro-AG Uniqueness and Upsert Logic for MongoDB collections micro_affinity_groups and micro_affinity_groups_processed.

Problem Statement
The current unique identifier for the documents sent to the endpoint `/v1/micro-affinity-groups` is the composite tuple of `(micro_ag_id, architecture_version, environment)`. To reflect the business reality, the application's unique constraint must be narrowed to exclude `architecture_version`, making `(micro_ag_id, environment)` the sole unique composite key.

The business rule dictates that within a given environment, a micro affinity group can be associated with exactly one `architecture_version`.

Architectural Assumptions & Dependencies
- External Index Management: Database-level unique compound indexes on `(micro_ag_id, environment)` are managed entirely outside the application. The application layer assumes these constraints exist or will be applied independently in MongoDB Atlas.

Requirements

1. Application Logic Update: Modify the `/v1/micro-affinity-groups` endpoint write/upsert operations. The Python database access layer must match, overwrite, or update existing records in the collections `micro_affinity_groups` and `micro_affinity_groups_processed` based exclusively on the `micro_ag_id` and `environment` fields.

2. Validation Alignment: Update schemas and Pydantic models as necessary to reflect the fact that the pair `micro_ag_id` and `environment` is the application-side identity used for MAG record matching and upsert lookup, without changing unrelated payload fields.

3. Preservation Guardrail: The only application change should be the document match criteria and structural validation of the query keys. All other application functionality—such as the validation of the `architecture_version` field itself within the payload—must remain completely untouched.

Out of Scope
- Creating, altering, or dropping MongoDB collection indexes programmatically within the application code.
- Migrating historical collections or writing cold-storage extraction scripts for older versions.
- Changing the schema properties of the document payload outside of the identity lookup fields."

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

### Session 2026-05-17

- Q: What should the service do if duplicate existing records are found for the same `micro_ag_id` and `environment`? → A: Reject the write with an application error if multiple existing records match the same pair.
- Q: What client-visible error semantics should duplicate existing records use? → A: Return `409 Conflict` when duplicate existing records are detected for the same identity pair.
- Q: When a matching identity pair already exists, should the service replace or merge the stored documents? → A: Fully replace the existing raw and processed documents for the matched `micro_ag_id` and `environment` pair.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Overwrite By MAG And Environment (Priority: P1)

As a service owner, I want raw and processed micro affinity group records to be matched by
`micro_ag_id` and `environment` only so that one environment can have only one current document
pair for a given micro affinity group.

**Why this priority**: This is the core business rule change and the reason for the feature.

**Independent Test**: Can be fully tested by submitting two valid payloads with the same
`micro_ag_id` and `environment` but different `architecture_version` values and confirming that the
 service keeps only one raw record and one processed record for that pair.

**Acceptance Scenarios**:

1. **Given** an existing raw and processed document for a `micro_ag_id` and `environment` pair,
   **When** a new valid payload is submitted for the same pair with a different
   `architecture_version`, **Then** the existing raw and processed documents are overwritten rather
  than creating parallel records, and stale fields from the previously stored documents do not
  survive the overwrite.
2. **Given** a valid payload for a new `micro_ag_id` and `environment` pair, **When** the request
   is processed, **Then** the service creates one raw record and one processed record for that pair.

---

### User Story 2 - Preserve Payload Validation And Response Shape (Priority: P2)

As an API client, I want `architecture_version` to remain part of the payload contract and to be
validated exactly as before so that the business identity change does not alter the request and
response fields I send and receive.

**Why this priority**: The uniqueness rule is changing, but the payload contract must remain stable
outside the identity lookup behavior.

**Independent Test**: Can be fully tested by sending valid and invalid payloads and confirming that
the service still validates `architecture_version` and returns the submitted value in successful
responses.

**Acceptance Scenarios**:

1. **Given** a valid payload containing `architecture_version`, **When** the request succeeds,
   **Then** the response and persisted documents still contain that submitted `architecture_version`
   value.
2. **Given** a payload with an invalid `architecture_version`, **When** the request reaches the
   endpoint, **Then** the request is rejected using the existing validation behavior.

---

### User Story 3 - Keep Environment Isolation (Priority: P3)

As a service owner, I want the same `micro_ag_id` to continue coexisting across different
environments so that narrowing the uniqueness rule does not collapse distinct environment records.

**Why this priority**: The business rule narrows uniqueness, but environment remains part of the
identity boundary.

**Independent Test**: Can be fully tested by submitting valid payloads with the same
`micro_ag_id` but different `environment` values and confirming that each environment retains its
own raw and processed record pair.

**Acceptance Scenarios**:

1. **Given** a valid payload already exists for one environment, **When** a payload with the same
   `micro_ag_id` is submitted for a different environment, **Then** the service stores a separate
   raw and processed document pair for the second environment.

### Edge Cases

- A submission with the same `micro_ag_id` and `environment` but a changed `architecture_version`
  must replace the existing record pair instead of creating duplicates.
- Replacing an existing record pair must fully overwrite the stored raw and processed documents
  rather than preserving unspecified fields from a previous version.
- If multiple existing raw or processed records already match the same `micro_ag_id` and
  `environment`, the service must reject the write rather than updating an arbitrary or partial set
  of duplicates, and the API response must signal that condition as a conflict.
- If exactly one matching record exists in only one of the two MAG collections for a
  `micro_ag_id` and `environment` pair, the service must treat that state as recoverable and
  repair it through the normal transactional overwrite path.
- A submission missing either `micro_ag_id` or `environment` must continue to fail validation.
- If a raw write and processed write occur in one transaction, the narrowed identity rule must not
  introduce partial-update behavior.
- Historical duplicate records for the same `micro_ag_id` and `environment` are out of scope and
  are not cleaned up by this feature.
- External database indexes may be absent in lower environments; application behavior still only
  changes lookup criteria and does not manage indexes directly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST match raw micro affinity group writes using only
  `micro_ag_id` and `environment`.
- **FR-002**: The application MUST match processed micro affinity group writes using only
  `micro_ag_id` and `environment`.
- **FR-003**: A successful submission with the same `micro_ag_id` and `environment` as an existing
  record MUST overwrite the existing raw and processed records even when `architecture_version`
  differs.
- **FR-003c**: Overwriting an existing record pair MUST fully replace the stored raw and processed
  documents for that `micro_ag_id` and `environment` pair rather than merging new values into older
  stored fields.
- **FR-003a**: If more than one existing raw or processed record matches the same `micro_ag_id`
  and `environment`, the application MUST reject the write with an application error rather than
  updating an arbitrary record or all duplicates.
- **FR-003b**: When the application rejects a write because duplicate existing records match the
  same `micro_ag_id` and `environment`, the HTTP API MUST return `409 Conflict`.
- **FR-003d**: If exactly one matching record exists in only one of `micro_affinity_groups` or
  `micro_affinity_groups_processed` for a `micro_ag_id` and `environment` pair, the application
  MUST repair that partial state by completing a normal transactional overwrite rather than
  returning conflict.
- **FR-004**: A successful submission with the same `micro_ag_id` but a different `environment`
  MUST remain a separate record pair.
- **FR-005**: The request payload MUST continue to require and validate `architecture_version`
  exactly as before.
- **FR-006**: Successful responses and newly persisted documents MUST continue to include the
  submitted `architecture_version` value.
- **FR-007**: The generated or maintained inbound contract models associated with
  `/v1/micro-affinity-groups` MUST preserve the existing payload field set and validation rules
  while any related contract descriptions or documentation reflect that `micro_ag_id` and
  `environment` are the MAG write-identity pair.
- **FR-008**: The feature MUST preserve existing route paths, status-code semantics, enrichment
  behavior, and transactional write behavior aside from the narrowed match criteria.
- **FR-009**: The application MUST NOT create, alter, or drop MongoDB indexes as part of this
  feature.
- **FR-010**: The feature MUST NOT migrate or rewrite historical records outside the normal new
  write path.
- **FR-011**: Automated regression coverage MUST prove overwrite behavior for same
  `micro_ag_id` plus `environment`, coexistence across environments, and unchanged validation for
  invalid payloads.

### Key Entities *(include if feature involves data)*

- **Micro Affinity Group Identity Pair**: The pair of `micro_ag_id` and `environment` that now
  uniquely identifies one logical raw record and one logical processed record in application
  behavior.
- **Raw Micro Affinity Group Record**: The unprocessed document written to
  `micro_affinity_groups` and matched by the identity pair.
- **Processed Micro Affinity Group Record**: The enriched document written to
  `micro_affinity_groups_processed` and matched by the identity pair.

## Assumptions

- MongoDB Atlas index management for the narrowed unique key is handled outside the application.
- The feature changes only application-side record matching and associated validation alignment,
  not the externally visible payload fields other than their identity semantics.
- Existing business rules for enrichment and error handling remain authoritative and unchanged.
- Historical duplicate data for the narrowed identity pair is outside the scope of this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In regression testing, submitting two valid payloads with the same `micro_ag_id` and
  `environment` but different `architecture_version` values results in exactly one raw record and
  one processed record for that pair.
- **SC-002**: In regression testing, submitting the same `micro_ag_id` to two different
  environments results in separate successful records for each environment.
- **SC-003**: 100% of regression cases covering invalid identity fields or invalid
  `architecture_version` continue to fail using existing validation semantics.
- **SC-003a**: In regression testing, a write attempted against pre-existing duplicate records for
  the same `micro_ag_id` and `environment` fails deterministically instead of silently modifying one
  or more duplicates.
- **SC-003b**: In regression testing, duplicate existing records for the same identity pair produce
  an HTTP `409 Conflict` response.
- **SC-003c**: In regression testing, an overwrite for an existing identity pair results in stored
  raw and processed documents that match the new submission and enrichment output without retaining
  stale fields from the prior version.
- **SC-004**: The required non-perf functional regression suite passes without requiring behavior
  changes in unrelated endpoints.