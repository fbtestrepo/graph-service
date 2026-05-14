# Feature Specification: Micro Affinity Group Relationship Enrichment

**Feature Branch**: `008-add-mag-relationships`  
**Created**: 2026-05-06  
**Status**: Draft  
**Input**: User description: "Enhance the existing micro-affinity-group endpoint by adding the following functionality:

Create and persist transformed version of the incoming JSON file. In addition to the original content the transformed JSON document has a new \"relationships\" element that captures the outgoing relationships of the micro affinity group workloads. A sample of what the transformed file should look like is provided here specs/samples/micro-affinity-group/micro-affinity-group-relationships.json

The \"relationships\" element is a list of source/target workload pairs.

The logic to construct this list is:
for each workload element in micro affinity group, find the corresponding architecture document by matching
architecture.metadata.AssetID == workload.parent-asset-id and
architecture.metadata.version == workload.architecture-version

If match fails return 422 Unprocessable entity status.

In the matched architecture document find a node where:
node-type is \"service\"
metadata.code-repo matches the workload.id
metadata.asset-id matches the workload.asset-id

This is the SOURCE workload/service.

If match fails return 422 Unprocessable entity status.

Using the matched service node unique-id search the same architecture document for an element in the \"relationships\" list where service node unique-id == relationship-type.connects.source.node

If no match proceed to the next workload.

If matching relationship is found:

using the relationship-type.connects.destination.node search the same architecture document for a node with unique-id == relationship-type.connects.destination.node

This is the DESTINATION workload/service.

If match fails return 422 Unprocessable entity status

Using the matched source and destination nodes construct the relationships element as
source-workload.id = source service node metadata.code-repo
source-workload.asset-id = source service node metadata.asset-id
destination-workload.id = destination service node metadata.code-repo
destination-workload.asset-id = destination service node metadata.asset-id

Add the relationship element to the relationship list."

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

### Session 2026-05-06

- Q: Should generated relationships include destinations outside the submitted micro affinity group? → A: Include every resolved outgoing relationship from each submitted workload, even when the destination workload is not part of the submitted micro affinity group.
- Q: Which fields should be used for the architecture lookup during enrichment? → A: Use the submission's top-level `parent-asset-id` and `architecture-version` for every workload lookup.
- Q: What qualifies as a valid destination node for a generated relationship? → A: The destination node must be a `service` node, and its `metadata.code-repo` and `metadata.asset-id` are used for `destination-workload`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Persist Enriched Group Document (Priority: P1)

As a service client, I want a successful micro affinity group submission to be stored as an enriched document so that the saved record includes the original workload membership plus its discovered outgoing workload relationships.

**Why this priority**: The main business value of this enhancement is that each accepted submission now produces a relationship-aware stored document rather than a membership-only record.

**Independent Test**: Can be fully tested by submitting a valid micro affinity group whose workloads resolve to architecture relationships, then verifying that the stored and returned document includes a `relationships` list derived from the matching architecture.

**Acceptance Scenarios**:

1. **Given** a valid micro affinity group submission whose workloads resolve to matching service nodes and at least one outgoing relationship in the corresponding application architecture, **When** the client submits it `to POST /micro-affinity-groups`, **Then** the service stores the validated raw submission in micro-affinity-groups, stores the transformed document with its `relationships` list in micro-affinity-groups-processed, and returns the stored transformed document.

2. **Given** a valid micro affinity group submission whose workloads resolve successfully but none of those workloads have outgoing relationships in the corresponding application architecture, **When** the client submits it, **Then** the service stores and returns the transformed document with an empty `relationships` list.

---

### User Story 2 - Reject Unresolvable Relationship Transformation (Priority: P2)

As a service client, I want the submission to fail when relationship enrichment cannot be resolved consistently so that the service never stores a partially transformed or ambiguous document.

**Why this priority**: Relationship data is only trustworthy if the service rejects submissions when the required architecture lookup, source service resolution, or destination service resolution fails.

**Independent Test**: Can be fully tested by submitting otherwise valid documents whose source or destination relationship lookups fail, then verifying that the request is rejected and nothing is stored.

**Acceptance Scenarios**:

1. **Given** a submitted workload whose parent asset and architecture version do not identify a matching application architecture document, **When** the client submits the document, **Then** the service rejects the request with `422 Unprocessable Entity` and does not store any record.
2. **Given** a submitted workload whose matching application architecture exists but does not contain a service node matching that workload's repository and asset identifiers, **When** the client submits the document, **Then** the service rejects the request with `422 Unprocessable Entity` and does not store any record.
3. **Given** a submitted workload whose resolved source service has an outgoing architecture relationship but the destination node referenced by that relationship cannot be resolved to a valid destination service workload, **When** the client submits the document, **Then** the service rejects the request with `422 Unprocessable Entity` and does not store any record.
4. **Given** a valid submission whose raw write succeeds but whose processed write fails during the same request, **When** the client submits the document, **Then** the service rejects the request and neither the raw record nor the processed record is persisted. The service returns 500 Internal Server Error.

---

### User Story 3 - Preserve Overwrite Semantics With Enriched Content (Priority: P3)

As a service client, I want repeated submissions for the same micro affinity group identity to overwrite the previous enriched record so that the stored document always reflects the latest accepted payload and its recomputed relationships.

**Why this priority**: The existing endpoint already supports deterministic overwrite behavior, and this enhancement must preserve that behavior after transformation is added.

**Independent Test**: Can be fully tested by submitting two valid documents with the same unique identity and verifying that only one stored enriched record remains and that its `relationships` data reflects the latest accepted submission.

**Acceptance Scenarios**:

1. **Given** an existing stored micro affinity group record with the same `micro-ag-id`, `environment`, and `architecture-version` as a new valid submission, **When** the client submits the new document, **Then** the service fully replaces the stored record with a newly transformed document and returns the stored replacement.
2. **Given** a valid submission that differs from an existing record by `environment` or `architecture-version`, **When** the client submits it, **Then** the service stores it as a separate enriched record instead of overwriting the existing one.

### Edge Cases

- A valid request includes workloads that resolve to service nodes but none of those service nodes have outgoing relationships in the matching architecture.
- A single source workload has multiple outgoing relationships in the matching architecture.
- Multiple submitted workloads resolve to outgoing relationships that point to the same destination workload.
- A submitted workload resolves to an outgoing relationship whose destination workload is not part of the submitted micro affinity group.
- A matching architecture relationship points to a destination node that is not a `service` node.
- A matching architecture relationship points to a destination service node that lacks the data needed to identify a destination workload.
- The client submits a request body that includes a `relationships` field even though relationships are server-generated output.
- The source workload lookup succeeds for some submitted workloads but fails for another workload in the same request.
- The same micro affinity group identity is re-submitted after the underlying architecture relationships have changed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST continue to expose `POST /micro-affinity-groups` as the submission endpoint for micro affinity group documents.
- **FR-002**: The request contract for `POST /micro-affinity-groups` MUST remain the existing micro affinity group input shape and MUST NOT require clients to supply a `relationships` field.
- **FR-003**: The system MUST reject any request that includes a client-supplied `relationships` field.
- **FR-004**: For each submitted workload, the system MUST use the submission's top-level `parent-asset-id` and top-level `architecture-version` values to locate the corresponding application architecture document used for enrichment.
- **FR-005**: If the corresponding application architecture document cannot be found for any submitted workload, the system MUST reject the request with `422 Unprocessable Entity` and MUST NOT persist any record.
- **FR-006**: For each submitted workload, the system MUST resolve a source service node in the matched application architecture whose `node-type` identifies a service and whose repository and asset identifiers match the submitted workload.
- **FR-007**: If the source service node cannot be resolved for any submitted workload, the system MUST reject the request with `422 Unprocessable Entity` and MUST NOT persist any record.
- **FR-008**: For each resolved source service node, the system MUST inspect the matched application architecture's relationship data for outgoing relationships whose source node identifier equals that source service node's unique identifier.
- **FR-009**: If a resolved source service node has no outgoing relationships in the matched application architecture, the system MUST continue processing the remaining submitted workloads without rejecting the request.
- **FR-010**: For each matched outgoing relationship, the system MUST resolve the destination node referenced by that relationship within the same application architecture document.
- **FR-011**: A destination node is only valid for relationship generation when its `node-type` identifies a service.
- **FR-012**: If an outgoing relationship references a destination node that cannot be resolved to a valid destination service workload, the system MUST reject the request with `422 Unprocessable Entity` and MUST NOT persist any record.
- **FR-013**: For each successfully resolved outgoing relationship, the system MUST add one relationship entry to the transformed document.
- **FR-014**: Each generated relationship entry MUST contain `source-workload` and `destination-workload` objects.
- **FR-015**: Each generated `source-workload` object MUST contain the repository identifier and asset identifier of the resolved source service node.
- **FR-016**: Each generated `destination-workload` object MUST contain the repository identifier and asset identifier of the resolved destination service node.
- **FR-017**: The transformed document MUST preserve all original accepted micro affinity group fields and append a top-level `relationships` list.
- **FR-018**: The `relationships` list MUST contain one entry for each resolvable outgoing relationship discovered from the submitted workloads in the matched application architecture documents, even when the resolved destination workload is not part of the submitted micro affinity group.
- **FR-019**: When no outgoing relationships are discovered for any submitted workload, the transformed document MUST contain an empty `relationships` list.
- **FR-020**: The system MUST log the outcome of each relationship search performed during transformation, including successful relationship resolution and the case where a valid source workload has no outgoing relationships.
- **FR-021**: For valid submissions, the system MUST persist the validated raw request payload in the `micro-affinity-groups` collection.
- **FR-022**: For valid submissions, the system MUST persist the transformed document in the `micro-affinity-groups-processed` collection.
- **FR-023**: A successful submission MUST return the stored transformed document in the response body.
- **FR-024**: The unique-record identity and overwrite behavior for both raw and processed micro affinity group records MUST remain the exact combination of `micro-ag-id`, `environment`, and `architecture-version`.
- **FR-025**: When a valid submission matches an existing record with the same unique identity, the system MUST fully overwrite both the stored raw record and the stored transformed record with newly computed values.
- **FR-026**: When a valid submission differs from an existing record by `environment` or `architecture-version`, the system MUST store both raw and transformed records as separate variants.
- **FR-027**: Requests rejected because relationship enrichment cannot be resolved consistently MUST return `422 Unprocessable Entity`.
- **FR-028**: The feature MUST include automated tests covering successful transformation with discovered relationships, successful transformation with no discovered relationships, missing architecture rejection, missing source service rejection, unresolved destination-service rejection, rejection of client-supplied `relationships`, overwrite behavior, and coexistence of different unique keys.
- **FR-029**: The feature MUST preserve the current separation of request validation, relationship-enrichment business rules, persistence logic, and HTTP error mapping within the existing service architecture.

- **FR-030**: The system MUST execute raw persistence, relationship transformation, and processed persistence as a single transactional unit of work.
- **FR-031**: If any persistence or transformation step fails after processing begins, the system MUST roll back the transaction so neither `micro-affinity-groups` nor `micro-affinity-groups-processed` contains a partial update for that submission.
- **FR-032**: Requests rejected because the processed persistence step fails MUST leave no partial raw or processed record behind.
- **FR-033**: Requests rejected because the processed persistence step fails after processing begins MUST return 500 Internal Server Error.


## Assumptions

- This enhancement changes the stored representation of accepted submissions but does not add a new endpoint, retrieval flow, or alternate submission format.
- The incoming request body continues to use the existing micro affinity group payload shape; `relationships` is derived output only.
- The submission's top-level parent asset identifier and top-level architecture version are the only lookup inputs used for resolving every submitted workload against application architecture data.
- A destination node is considered a valid destination workload only when it is a `service` node and can provide both a repository identifier and an asset identifier for the generated relationship entry.
- The transformed `relationships` list preserves all resolvable outgoing relationships represented in the matched architecture data, including relationships whose destinations are outside the submitted micro affinity group; if the same destination is reached by multiple resolved outgoing relationships, each relationship is retained as a separate list entry.
- If any required relationship-enrichment lookup fails, the entire request is rejected rather than storing a partially enriched document.
- Successful processing stores two synchronized representations of the same accepted submission: the validated raw request in micro-affinity-groups and the transformed projection in micro-affinity-groups-processed.

### Key Entities *(include if feature involves data)*

- **Micro Affinity Group Submission**: The client-provided micro affinity group document before enrichment, containing group identity, environment metadata, and the submitted workloads.
- **Enriched Micro Affinity Group Record**: The stored representation of an accepted submission, consisting of the original submission fields plus the generated `relationships` list.
- **Relationship Entry**: A generated source-to-destination workload pair derived from one outgoing architecture relationship and represented as `source-workload` and `destination-workload` objects.
- **Source Service Node**: The service node in an application architecture document that matches a submitted workload and serves as the origin of outgoing relationships.
- **Destination Workload**: The workload representation derived from the destination service node referenced by a matched outgoing architecture relationship.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In acceptance testing, 100% of valid submissions with resolvable outgoing workload relationships write the raw payload to `micro-affinity-groups`, write the transformed payload to `micro-affinity-groups-processed`, and return the transformed document with a `relationships` list matching the architecture-derived source and destination workload pairs.
- **SC-002**: In acceptance testing, 100% of valid submissions whose workloads have no outgoing relationships are stored successfully with an empty `relationships` list.
- **SC-003**: In acceptance testing, 100% of submissions with missing architecture matches, missing source service matches, or unresolved relationship destinations are rejected with no record written or overwritten.
- **SC-004**: In acceptance testing, re-submitting the same unique key overwrites the existing enriched record in 100% of cases, while submissions with a different environment or architecture version coexist in 100% of cases.
- **SC-005**: In automated verification, the feature includes coverage for all primary enrichment success paths, rejection paths, and overwrite/coexistence outcomes defined in this specification.
- **SC-006**: In acceptance testing, 100% of failures during the transactional raw-write plus processed-write flow leave no partial record in either target collection.