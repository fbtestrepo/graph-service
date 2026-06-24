# Feature Specification: Workload Test Scope Endpoint

**Feature Branch**: `016-workload-test-scope`  
**Created**: 2026-06-23  
**Status**: Draft  
**Input**: User description: "Add a POST endpoint at /v1/micro-affinity-groups/workloads/test-scope that computes affected workload relationships and summary statistics for changed workloads within a required environment filter."

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
- **Traversal error semantics**: For graph-traversal or graph-resolution endpoints, `404` MUST be
  used only when the primary resource named in the URL path does not exist; if that resource
  exists but downstream graph resolution fails because dependent records are missing or corrupted,
  the system MUST return `422 Unprocessable Entity`.
- **Immutable structure**: Do not add/remove/rename folders from the baseline structure.

## Clarifications

### Session 2026-06-23

- Q: How should unresolved related workloads (missing resolvable `micro_ag_id` for a relationship endpoint) be handled? → A: Exclude unresolved relationships and add unresolved workload asset IDs to `unknown_workloads`.
- Q: How should duplicate `changed_workloads` input IDs be handled? → A: Deduplicate by `workload_asset_id` and preserve first-seen input order in output arrays.
- Q: How should the endpoint behave when the environment filter matches no records? → A: Return `200` with empty `affected_workload_relationships`, all deduplicated input IDs in `unknown_workloads`, and summary totals derived from the response payload.
- Q: How should `affected_workload_relationships` ordering be defined? → A: After deduplication, sort lexicographically by (`source_workload.workload_asset_id`, `destination_workload.workload_asset_id`).
- Q: How should a missing or blank `environment` query parameter be handled? → A: Return `422` validation error and perform no processing.

## User Scenarios & Testing *(mandatory)*
### User Story 1 - Build Test Scope For Changed Workloads (Priority: P1)

As an API consumer, I want to submit a list of changed workload asset IDs for a specific environment and receive the resolved affected workload relationships, so I can identify what test scope is impacted by recent changes.

**Why this priority**: This is the core business outcome of the feature and the reason the endpoint exists.

**Independent Test**: Send a valid POST request with `environment` and known `changed_workloads`, then verify that resolved `changed_workloads`, unique `affected_workload_relationships`, and `summary` are returned in snake_case and align with source data.

**Acceptance Scenarios**:

1. **Given** an environment with relationship records and a request containing known workload asset IDs, **When** the endpoint is called, **Then** the response includes the same environment, resolved `changed_workloads`, unique `affected_workload_relationships`, and summary totals computed from the returned data.
2. **Given** a changed workload that appears as both relationship source and destination across records, **When** the endpoint is called, **Then** all qualifying relationships are included exactly once in `affected_workload_relationships`.

---

### User Story 2 - Detect Unknown Workloads (Priority: P2)

As an API consumer, I want input workloads that do not appear in environment-scoped relationship records to be listed as unknown, so I can quickly identify unresolved or invalid workload inputs.

**Why this priority**: Unknown workload visibility prevents silent data-quality issues and supports correction workflows.

**Independent Test**: Send a request that includes both known and unknown workload IDs and verify unknown items appear in `unknown_workloads` while known items are processed normally.

**Acceptance Scenarios**:

1. **Given** an input workload asset ID that appears in neither source nor destination relationships for the specified environment, **When** the endpoint is called, **Then** the workload is included in `unknown_workloads` with object format `{"workload_asset_id": "..."}`.
2. **Given** a mixed request of known and unknown workloads, **When** the endpoint is called, **Then** known workloads contribute to changed and affected sections while unknown workloads only appear in `unknown_workloads`.

---

### User Story 3 - Preserve Contract Shape And Casing (Priority: P3)

As an API consumer, I want the response payload to consistently follow the documented JSON structure and snake_case key casing, so I can integrate reliably without custom per-response normalization.

**Why this priority**: A stable response contract reduces integration defects and downstream parser complexity.

**Independent Test**: Validate a successful response against the expected schema shape from the sample output contract and verify all returned keys are snake_case.

**Acceptance Scenarios**:

1. **Given** a valid request, **When** the endpoint responds successfully, **Then** the payload shape includes `environment`, `changed_workloads`, `affected_workload_relationships`, `unknown_workloads`, and `summary` in snake_case and with expected nesting.
2. **Given** repeated requests with the same inputs and source data, **When** responses are compared, **Then** the set of returned relationships and summary totals is consistent.

### Edge Cases

- The request contains duplicate `workload_asset_id` entries in `changed_workloads`; processing is deduplicated by first-seen `workload_asset_id` order.
- A changed workload appears only as a relationship source and never as a destination.
- A changed workload appears only as a relationship destination and never as a source.
- A relationship endpoint workload asset ID resolves to more than one owning micro affinity group in the same environment.
- Multiple changed workloads resolve to overlapping relationship pairs that would otherwise be duplicated.
- A changed workload exists in relationship records, but one related endpoint workload has no resolvable micro affinity group in the filtered dataset; such relationships are excluded and unresolved endpoint workloads are reported as unknown.
- The environment filter is valid but returns no matching records; the endpoint still returns `200` with no affected relationships and all deduplicated input workload IDs marked unknown.
- The request contains an empty `changed_workloads` list.
- The `environment` query parameter is missing or blank; request is rejected with validation error and no data processing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose a POST endpoint at `/v1/micro-affinity-groups/workloads/test-scope`.
- **FR-002**: The endpoint MUST require query parameter `environment` and apply it as a global filter to every data lookup used to build the response.
- **FR-003**: The request body MUST accept `changed_workloads` as a list of objects, where each object contains `workload_asset_id`.
- **FR-004**: The successful response payload MUST use snake_case for all JSON keys.
- **FR-005**: The successful response payload MUST include `environment`, `changed_workloads`, `affected_workload_relationships`, `unknown_workloads`, and `summary`.
- **FR-006**: The successful response contract MUST align with the documented output format in `specs/samples/micro-affinity-group/workload/test-scope.json`.
- **FR-007**: For each input `workload_asset_id`, the system MUST evaluate relationship records where the workload appears as `source_workload.asset_id`.
- **FR-008**: For each source-side relationship found by FR-007, the source `micro_ag_id` MUST be taken from the matching relationship record.
- **FR-009**: For each source-side relationship found by FR-007, the destination workload `micro_ag_id` MUST be resolved by finding the relationship record where `source_workload.asset_id` equals that destination workload asset ID.
- **FR-010**: For each input `workload_asset_id`, the system MUST evaluate relationship records where the workload appears as `destination_workload.asset_id`.
- **FR-011**: For each destination-side relationship found by FR-010, the destination workload `micro_ag_id` MUST be resolved by finding the relationship record where `source_workload.asset_id` equals that destination workload asset ID.
- **FR-012**: For each destination-side relationship found by FR-010, the source workload `micro_ag_id` MUST be taken from the relationship record where `source_workload.asset_id` equals that source workload asset ID.
- **FR-013**: The system MUST append fully resolved relationship objects to `affected_workload_relationships` for both source-side and destination-side matches.
- **FR-014**: `affected_workload_relationships` MUST contain unique relationship entries only, with duplicates removed across all match paths.
- **FR-015**: For each input `workload_asset_id` that has no source-side or destination-side matches in the filtered dataset, the system MUST add `{ "workload_asset_id": "..." }` to `unknown_workloads`.
- **FR-015a**: If a relationship candidate cannot be fully resolved because either source or destination workload cannot be mapped to a `micro_ag_id` in the environment-filtered dataset, the system MUST exclude that relationship from `affected_workload_relationships`.
- **FR-015b**: For each unresolved workload endpoint excluded by FR-015a, the system MUST add `{ "workload_asset_id": "..." }` to `unknown_workloads` if it is not already present.
- **FR-015c**: If workload ownership resolution returns more than one candidate `micro_ag_id` for the same relationship endpoint workload asset ID in the requested environment, the system MUST return `422 Unprocessable Entity` and stop test-scope resolution processing.
- **FR-016**: The response `changed_workloads` MUST include each known input workload with both `workload_asset_id` and resolved `micro_ag_id`.
- **FR-017**: The response `summary.total_affected_workload_relationships` MUST equal the total number of items in `affected_workload_relationships`.
- **FR-018**: The response `summary.total_affected_workloads` MUST equal the number of distinct workload asset IDs across all source and destination workloads in `affected_workload_relationships`.
- **FR-019**: The response `summary.total_affected_micro_ags` MUST equal the number of distinct micro affinity group IDs across all source and destination workloads in `affected_workload_relationships`.
- **FR-020**: The response `summary.total_unknown_workloads` MUST equal the number of items in `unknown_workloads`.
- **FR-021**: The response MUST report the same `environment` value provided in the request query parameter.
- **FR-022**: The response MUST include a generation timestamp field in snake_case consistent with the sample contract.
- **FR-023**: When `changed_workloads` is empty, the endpoint MUST return empty `changed_workloads`, `affected_workload_relationships`, and `unknown_workloads` lists with summary counts of zero.
- **FR-024**: Input `changed_workloads` MUST be deduplicated by `workload_asset_id` for processing, preserving first-seen input order.
- **FR-025**: The response `changed_workloads` and `unknown_workloads` arrays MUST each contain unique `workload_asset_id` entries and preserve first-seen input order among included items.
- **FR-026**: If the specified `environment` has no matching relationship records, the endpoint MUST return `200 OK` with an empty `affected_workload_relationships` array.
- **FR-027**: In the no-matching-records case from FR-026, `unknown_workloads` MUST contain all deduplicated input `workload_asset_id` values in first-seen input order, and `changed_workloads` MUST be empty.
- **FR-028**: In the no-matching-records case from FR-026, all `summary` values MUST be computed from the returned payload and remain internally consistent.
- **FR-029**: After deduplication, `affected_workload_relationships` MUST be sorted lexicographically by (`source_workload.workload_asset_id`, `destination_workload.workload_asset_id`).
- **FR-030**: If `environment` is missing or blank, the endpoint MUST return `422 Unprocessable Entity` as a validation error and MUST NOT perform test-scope resolution processing.
- **FR-031**: For representative local smoke-test fixtures, the endpoint SHOULD meet latency targets of p95 <= 300 ms and p99 <= 600 ms.

## Assumptions

- Relationship records may be partially incomplete; when endpoint micro affinity group resolution is not possible, exclusion and unknown reporting behavior from FR-015a and FR-015b applies.
- Relationship ownership for any single endpoint workload asset ID is expected to be unambiguous within one environment; ambiguity triggers FR-015c failure behavior.
- If a workload appears in relationship records for the specified environment, it is considered known even if it appears only on one side (source or destination).
- When duplicate workloads are provided in the input, first-seen order determines their preserved output order.
- A valid request with an environment that has no matching records is treated as a successful no-data result, not an error condition.
- Distinct counting in summary fields is based on exact string equality of workload asset IDs and micro affinity group IDs.

## Dependencies

- Environment-scoped relationship data is available in the `micro_affinity_groups_processed` collection at request time.
- Existing API consumers rely on the documented sample response contract for parsing.
- The upstream dataset remains internally consistent enough to resolve required identifiers for returned relationship entries.

### Key Entities *(include if feature involves data)*

- **Test Scope Request**: Input containing `environment` and a list of `changed_workloads` with `workload_asset_id` values.
- **Changed Workload**: A workload from input that is recognized in environment-filtered relationship data and resolved to a `micro_ag_id`.
- **Affected Workload Relationship**: A unique source-to-destination workload pair with both workloads resolved to `workload_asset_id` and `micro_ag_id`.
- **Unknown Workload**: An input workload asset ID with no source-side or destination-side relationship match in the specified environment.
- **Summary**: Aggregate counts derived from affected relationships and unknown workloads.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a fixed dataset and identical request payload, 100% of repeated responses produce the same relationship set and summary totals.
- **SC-002**: In contract validation, 100% of successful responses include required top-level keys and use snake_case for all keys.
- **SC-003**: In acceptance tests with mixed known and unknown workload IDs, 100% of unknown inputs are reported in `unknown_workloads` and excluded from resolved `changed_workloads`.
- **SC-004**: In acceptance tests, summary totals match recomputed totals from response payload content with 100% accuracy.
- **SC-005**: In acceptance tests based on the sample relationship dataset, affected relationships are de-duplicated with zero duplicate entries in the final response.
- **SC-006**: In deterministic-ordering tests, `affected_workload_relationships` always appears sorted by (`source_workload.workload_asset_id`, `destination_workload.workload_asset_id`) for identical inputs and unchanged data.
- **SC-007**: In validation tests, requests with missing or blank `environment` return `422` and produce no response payload containing computed test-scope data.
- **SC-008**: In local smoke-performance validation with representative fixture data, measured endpoint latency is p95 <= 300 ms and p99 <= 600 ms.
