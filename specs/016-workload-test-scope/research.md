# Research: Workload Test Scope Endpoint

## Decision 1: Use targeted MongoDB aggregation for workload-to-MAG resolution

- Decision: Resolve affected relationships using environment-filtered MongoDB queries/aggregation that unwind relationships and join workload ownership by `workloads.asset_id`, instead of loading whole collections into memory.
- Rationale:
  - Satisfies the requirement to optimize workload-to-MAG matching in the database layer.
  - Preserves environment isolation by enforcing `environment` in every match/join stage.
  - Reduces risk of memory-heavy behavior on larger datasets.
- Alternatives considered:
  - Load all environment documents and resolve joins in Python: rejected due to unnecessary memory and CPU overhead.
  - Per-relationship N+1 lookups from core logic: rejected due to chatty I/O and avoidable latency.

## Decision 2: Resolve both source-side and destination-side relationship matches

- Decision: Build candidate relationship rows from two paths: where changed workload is relationship source and where it is relationship destination.
- Rationale:
  - Matches explicit feature behavior and captures dual-role workloads.
  - Ensures complete impact graph from changed workloads.
- Alternatives considered:
  - Source-only matching: rejected because destination-driven impact would be missed.
  - Destination-only matching: rejected because forward dependency impact would be missed.

## Decision 3: Handle unresolved endpoints by exclusion plus unknown reporting

- Decision: If either endpoint workload in a candidate relationship cannot resolve to a `micro_ag_id` in the same environment, exclude that relationship and add unresolved endpoint asset IDs to `unknown_workloads` (deduplicated).
- Rationale:
  - Aligns with clarified behavior in the feature spec.
  - Avoids partial/ambiguous relationship rows in `affected_workload_relationships`.
- Alternatives considered:
  - Emit null `micro_ag_id` values: rejected because it weakens contract quality.
  - Fail entire request on first unresolved row: rejected because it discards useful partial scope.

## Decision 4: Keep deterministic ordering and deduplication rules

- Decision:
  - Deduplicate input workload IDs by first-seen order.
  - Keep `changed_workloads` and `unknown_workloads` unique with first-seen order.
  - Deduplicate affected relationship rows by `(source_workload.workload_asset_id, destination_workload.workload_asset_id)` and then sort lexicographically by that pair.
- Rationale:
  - Produces stable, testable responses across repeated runs.
  - Prevents duplicate-driven summary inflation.
- Alternatives considered:
  - Preserve discovery order: rejected because database iteration order may vary.
  - Lexicographically sort all arrays: rejected for input-driven arrays where first-seen semantics are required.

## Decision 5: Missing/blank environment is a 422 validation failure

- Decision: A missing or blank `environment` query parameter returns `422` with validation error semantics and no test-scope processing.
- Rationale:
  - Consistent with constitution guidance and current validation/error-handling behavior.
  - Aligns with clarifications already accepted in the feature spec.
- Alternatives considered:
  - Return `400`: rejected due to clarified spec decision and existing validation model.
  - Default environment implicitly: rejected as unsafe and ambiguous.

## Decision 6: Treat environment no-data as successful empty-resolution payload

- Decision: If the environment filter matches no records, return `200` with empty `affected_workload_relationships`, empty `changed_workloads`, deduplicated input IDs in `unknown_workloads`, and internally consistent summary totals.
- Rationale:
  - No-data for an environment is a valid business outcome, not a malformed request.
  - Keeps client behavior predictable while preserving complete accounting of input IDs.
- Alternatives considered:
  - Return `404` or `422` for no-data environment: rejected because primary endpoint resource exists and request is valid.

## Decision 7: Test strategy prioritizes endpoint/use-case/persistence slices plus full regression

- Decision: Add comprehensive tests across endpoint, core use case, and persistence adapter behavior; then run the full suite and core purity check.
- Rationale:
  - Matches repository testing style and architecture boundaries.
  - Covers required happy paths, environment isolation, edge cases, summary math, and contract validation.
- Alternatives considered:
  - Endpoint-only tests: rejected because database query behavior needs persistence-level assertions.
  - Persistence-only tests: rejected because API contract behavior would remain under-validated.
