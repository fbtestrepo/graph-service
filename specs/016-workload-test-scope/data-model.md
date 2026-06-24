# Data Model: Workload Test Scope Endpoint

## Overview

This feature introduces a request/response model for workload test-scope resolution in an
environment-scoped micro affinity graph.

## Entity: TestScopeRequest

Represents one API request.

### Fields

- `environment` (string, required): Query parameter used as a global filter across all data access.
- `changed_workloads` (array of `ChangedWorkloadInput`, required): Input workload asset identifiers.

### Validation Rules

- `environment` must be non-empty after trimming.
- `changed_workloads` may be empty.
- Input workload IDs are deduplicated by first-seen order for processing.

## Entity: ChangedWorkloadInput

Represents one item in input `changed_workloads`.

### Fields

- `workload_asset_id` (string, required)

### Validation Rules

- Must be non-empty string.

## Entity: ResolvedChangedWorkload

Represents one known changed workload in response.

### Fields

- `workload_asset_id` (string, required)
- `micro_ag_id` (string, required)

### Validation Rules

- One entry per unique known input workload.
- Ordered by first appearance in deduplicated input.

## Entity: WorkloadEndpoint

Represents one endpoint of an affected relationship.

### Fields

- `workload_asset_id` (string, required)
- `micro_ag_id` (string, required)

## Entity: AffectedWorkloadRelationship

Represents one resolved workload-to-workload relationship affected by input changes.

### Fields

- `source_workload` (`WorkloadEndpoint`, required)
- `destination_workload` (`WorkloadEndpoint`, required)

### Validation Rules

- Entry uniqueness key: `(source_workload.workload_asset_id, destination_workload.workload_asset_id)`.
- Entries are sorted lexicographically by the same uniqueness key after deduplication.

## Entity: UnknownWorkload

Represents one workload asset ID that cannot be resolved for inclusion in scope.

### Fields

- `workload_asset_id` (string, required)

### Validation Rules

- Includes input workloads with no source-side or destination-side matches.
- Includes unresolved relationship endpoint workloads discovered during relationship resolution.
- Unique by `workload_asset_id`, preserving first-seen input-driven order.

## Entity: TestScopeSummary

Represents aggregate counters derived from response payload arrays.

### Fields

- `total_affected_workload_relationships` (integer >= 0)
- `total_affected_workloads` (integer >= 0)
- `total_affected_micro_ags` (integer >= 0)
- `total_unknown_workloads` (integer >= 0)

### Derivation Rules

- `total_affected_workload_relationships = len(affected_workload_relationships)`
- `total_affected_workloads = distinct count of source/destination workload_asset_id values`
- `total_affected_micro_ags = distinct count of source/destination micro_ag_id values`
- `total_unknown_workloads = len(unknown_workloads)`

## Entity: TestScopeResponse

Represents the full successful endpoint response.

### Fields

- `timestamp` (UTC string, required, `YYYY-MM-DDTHH:MM:SSZ`)
- `environment` (string, required)
- `changed_workloads` (array of `ResolvedChangedWorkload`, required)
- `affected_workload_relationships` (array of `AffectedWorkloadRelationship`, required)
- `unknown_workloads` (array of `UnknownWorkload`, required)
- `summary` (`TestScopeSummary`, required)

### Validation Rules

- All keys are snake_case.
- `environment` mirrors request query parameter.
- `summary` must remain internally consistent with payload arrays.

## Processing State Transitions

1. Validate request (`environment`, `changed_workloads`) in inbound adapter.
2. Deduplicate input workload IDs by first-seen order.
3. Query/aggregate environment-scoped source-side and destination-side relationship candidates.
4. Resolve source and destination endpoint `micro_ag_id` values by workload ownership in same environment.
5. Exclude unresolved relationship candidates; accumulate unresolved workload IDs into unknown set.
6. Build deduplicated, sorted `affected_workload_relationships`.
7. Build `changed_workloads` from known input workloads and resolved owner MAGs.
8. Build `unknown_workloads` from unmatched input workloads plus unresolved endpoints.
9. Compute summary counters directly from final payload arrays.
