# Research: Rename MongoDB Collection Names

**Branch**: 010-rename-collection-names  
**Date**: 2026-05-16

## Decisions

### Decision 1: Centralize collection identifiers inside the MongoDB adapter layer

- **Decision**: Add a single collection-name mapping module under `src/adapters/outbound/mongodb/`
  and have the affected MongoDB repositories consume named constants instead of repeating string
  literals.
- **Rationale**:
  - The current dashed collection names are hardcoded inline in only three outbound MongoDB
    repositories, so a local constants module keeps the change tightly scoped to the adapter layer.
  - One source of truth reduces the chance that repositories and persistence tests drift apart on
    the renamed identifiers.
  - This satisfies the review-readiness constraint by minimizing churn outside the data access layer.
- **Alternatives considered**:
  - Replace string literals inline without centralization: rejected because it leaves collection
    naming fragmented across files and increases future maintenance risk.
  - Introduce collection-name settings in application config: rejected because the names are static
    implementation details, not runtime configuration.

### Decision 2: Rename only the dashed collections already used by MongoDB adapters

- **Decision**: Limit the rename scope to the existing dashed MongoDB collections:
  `application-architectures`, `micro-affinity-groups`, and
  `micro-affinity-groups-processed`.
- **Rationale**:
  - Repository exploration shows these are the only collection identifiers in the data layer that
    still use dashes.
  - Collections such as `components` and `component_payload_records` are already compliant and
    should remain unchanged per the clarified spec.
  - Explicit scope control prevents unnecessary edits in unrelated adapters or tests.
- **Alternatives considered**:
  - Rename every collection constant regardless of current format: rejected because compliant names
    would incur needless churn without delivering feature value.
  - Broaden the change to API route names for consistency: rejected because the spec explicitly
    excludes endpoint changes.

### Decision 3: Treat the feature as a code-switch only, not a data migration

- **Decision**: Update application code and tests to point at underscore-based collection names
  without automatically migrating pre-existing dashed collections or their data.
- **Rationale**:
  - The clarification explicitly selected this behavior.
  - A code-only switch avoids introducing migration logic, bootstrap scripts, or operational state
    changes into the current feature.
  - This keeps planning and implementation focused on adapter alignment rather than deployment-time
    data movement.
- **Alternatives considered**:
  - Automatic migration of dashed collections to underscore collections: rejected by clarification.
  - Dual-read or dual-write support across old and new collection names: rejected because it would
    expand runtime behavior and code churn beyond the requested scope.

### Decision 4: Update only Mongo-backed persistence tests and shared fixture consumers

- **Decision**: Restrict test changes to persistence suites and shared fixtures that query MongoDB
  collections directly, while leaving endpoint and unit tests untouched unless they directly use
  collection names.
- **Rationale**:
  - The persistence suites directly seed and assert collection contents via
    `client.app.state.mongo_db.get_collection(...)`; these tests are the only ones that validate the
    collection contract.
  - Endpoint tests use fake repositories and are not sensitive to real MongoDB collection names.
  - This selective strategy minimizes churn and keeps the review focused on persistence alignment.
- **Alternatives considered**:
  - Sweep all tests for possible naming updates: rejected because most suites do not interact with
    MongoDB collections directly.
  - Ignore test collection-name assertions and rely only on repository changes: rejected because
    persistence tests would continue asserting against obsolete names.

### Decision 5: Use the non-perf functional pytest command as the required regression gate

- **Decision**: Treat `python -m pytest tests -v -k "not perf_smoke"` as the required functional
  regression gate for this feature and record the verified planning baseline of 81 passed,
  3 deselected.
- **Rationale**:
  - This command exercises endpoint, persistence, and unit/use-case coverage while excluding the
    opt-in non-functional perf smoke modules.
  - The user explicitly requested that all functional tests be run and show no regressions.
  - The command completed successfully in the active workspace, so it is a verified baseline.
- **Alternatives considered**:
  - Run only persistence tests: rejected because the full functional suite better proves that the
    collection rename stays isolated and does not affect broader behavior.
  - Run the full suite including perf smoke as the required gate: rejected because perf smoke tests
    are optional and not part of the functional definition.

## Open Questions

None. The migration behavior and scope boundaries are now resolved.