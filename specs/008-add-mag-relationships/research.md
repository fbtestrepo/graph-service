# Research: Micro Affinity Group Relationship Enrichment

**Branch**: 008-add-mag-relationships  
**Date**: 2026-05-06

## Decisions

### Decision 1: Preserve the existing raw-input write and add a separate processed-document upsert

- **Decision**: Keep the current `micro-affinity-groups` collection as the raw-input record of a
  successful request and add a second collection, `micro-affinity-groups-processed`, for the
  relationship-enriched projection returned by the endpoint. The enriched response body comes from
  the processed collection, while the existing raw collection is retained to avoid regressing the
  current write behavior.
- **Rationale**:
  - The planning prompt explicitly requires persisting raw input and separately upserting the
    transformed result.
  - Preserving the existing raw collection avoids breaking current readers, diagnostics, or tests
    that already depend on `micro-affinity-groups`.
  - Separating raw and processed storage keeps the enrichment output auditable and recomputable.
- **Alternatives considered**:
  - Replace `micro-affinity-groups` with the processed shape only: rejected because it conflicts
    with the prompt’s rollback requirements and risks regressions to existing persistence behavior.
  - Store raw and processed payloads in one wrapper document: rejected because it changes the
    established repository pattern and makes existing collection consumers harder to preserve.

### Decision 2: Put transformation logic in a dedicated pure core mapper/service

- **Decision**: Add a dedicated `MicroAffinityGroupRelationshipMapper` in `src/core/domain/` to
  compute the processed payload from a validated request plus the matching application
  architecture document. The use case orchestrates repository access and transactions, but the
  mapper owns the field-by-field transformation rules.
- **Rationale**:
  - The prompt explicitly asks for a distinct transformation component decoupled from persistence.
  - Keeping the mapper pure makes the relationship logic unit-testable without FastAPI or MongoDB.
  - It fits the constitution by keeping business rules in `src/core/` and adapters thin.
- **Alternatives considered**:
  - Inline the transformation inside the MongoDB repository: rejected because it mixes business
    rules with persistence logic.
  - Keep the transformation inside the router or use case only: rejected because it reduces reuse
    and makes the mapping rules harder to isolate in tests.

### Decision 3: Add a transaction manager port and use MongoDB client sessions for the full unit of work

- **Decision**: Introduce a core `TransactionManager` port implemented by a MongoDB adapter that
  uses `MongoClient.start_session()` plus `with_transaction(...)`. The use case will run raw
  persistence, architecture lookup, transformation, and processed upsert inside that transaction,
  and repository methods will accept an optional opaque session parameter so each MongoDB
  operation participates in the same transaction.
- **Rationale**:
  - The prompt requires all three operations to roll back together on failure.
  - Official MongoDB/PyMongo guidance requires session-bound operations for multi-operation
    transactions and supports `with_transaction(...)` as the retry-aware API.
  - A dedicated port keeps `pymongo` session details out of the core.
- **Alternatives considered**:
  - Depend on single-document atomicity only: rejected because the feature spans multiple writes
    across collections.
  - Start sessions directly in the use case: rejected because it violates core purity.

### Decision 4: Update integration tests to run against a replica-set-capable MongoDB fixture

- **Decision**: Adjust the MongoDB integration-test fixture so transaction tests run against a
  replica-set-capable MongoDB deployment, because MongoDB transactions require replica sets or
  sharded clusters.
- **Rationale**:
  - Official MongoDB documentation states that multi-document transactions are supported on
    replica sets and sharded clusters, not standalone deployments.
  - The feature’s rollback test is not credible unless the test fixture can actually execute
    transactions.
  - This keeps the transaction design honest before implementation begins.
- **Alternatives considered**:
  - Keep the current standalone container fixture and mock transactions: rejected because it would
    not validate real rollback behavior.
  - Skip transaction integration tests entirely: rejected because rollback is a primary technical
    requirement.

### Decision 5: Keep the request contract unchanged and add a separate processed response contract

- **Decision**: Preserve the existing micro affinity group request schema and add a new processed
  response schema that mirrors the sample transformed output, including a required top-level
  `relationships` list. Implementation should promote the finalized response schema into
  `specs/001-service-skeleton/contracts/` and generate a dedicated
  `micro_affinity_group_processed.py` response model.
- **Rationale**:
  - The spec explicitly keeps `relationships` as server-generated output only.
  - A distinct response contract documents the changed API surface without destabilizing the
    existing request model and validator flow.
  - This fits the repo’s spec-driven codegen workflow and schema README mapping pattern.
- **Alternatives considered**:
  - Reuse the request schema for the response: rejected because the response now has a required
    `relationships` field.
  - Hand-write the response model without a schema: rejected because it increases contract drift
    risk.

### Decision 6: Treat processed-record identity as the existing composite unique key

- **Decision**: Upsert processed documents by the same effective record identity already used by
  the raw collection: `micro-ag-id + environment + architecture-version`.
- **Rationale**:
  - The existing endpoint semantics and clarified spec both define overwrite/coexistence on the
    composite key, not `micro-ag-id` alone.
  - Reusing the same identity rule avoids creating divergent behavior between raw and processed
    collections.
  - It still satisfies the prompt’s idempotency requirement for repeated submissions of the same
    group identity in context.
- **Alternatives considered**:
  - Upsert processed documents by `micro-ag-id` only: rejected because it would collapse
    environment/version variants and introduce regressions.
  - Insert processed documents without upsert: rejected because it breaks idempotency.

### Decision 7: Log every relationship search from the use case/mapper with Python standard logging

- **Decision**: Use the Python standard-library `logging` module in the transformation path to log
  each relationship search outcome, including source-service match success, outgoing-relationship
  no-match cases, and successful destination-service resolution.
- **Rationale**:
  - The repo has no existing custom observability abstraction, so standard logging is the smallest
    aligned choice.
  - Logging at the transformation boundary captures both successful searches and “no match” cases
    without changing persistence contracts.
  - Standard logging is allowed in the core and keeps the design simple.
- **Alternatives considered**:
  - Add a new logging port: rejected because the repo currently has no such pattern and it adds
    complexity beyond the prompt’s need.
  - Log only failures: rejected because the prompt explicitly requires logging every relationship
    search result.

### Decision 8: Extend the existing use case and test split rather than inventing a parallel pipeline

- **Decision**: Evolve the current `UpsertMicroAffinityGroup` use case and surrounding tests so
  the endpoint keeps the same URL and request validation path while gaining a mapper, transaction
  manager, processed repository, and rollback/idempotency test cases.
- **Rationale**:
  - This reuses the working route/repository/error-mapping patterns already established by feature
    007.
  - It minimizes regression risk and keeps the endpoint’s public shape stable.
  - The prompt asks to avoid regressions to existing functionality.
- **Alternatives considered**:
  - Create a second endpoint or second orchestration flow: rejected because it duplicates the
    existing contract and invites drift.
  - Replace the raw-write behavior entirely: rejected because it violates the additive persistence
    requirement.

## Open Questions

None that block Phase 1 design.