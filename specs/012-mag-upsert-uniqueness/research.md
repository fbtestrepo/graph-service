# Research: MAG Upsert Uniqueness

**Branch**: 012-mag-upsert-uniqueness  
**Date**: 2026-05-17

## Decisions

### Decision 1: Align repository contracts with the new identity pair

- **Decision**: Update the MAG repository port APIs so write identity is expressed as
  `micro_ag_id + environment` only, while `architecture_version` remains part of the payload and
  of the application-architecture enrichment lookup.
- **Rationale**:
  - The existing port signatures and docstrings still describe the old three-field identity.
  - Keeping a no-longer-relevant `architecture_version` argument in the upsert signatures would
    obscure the feature’s core rule and weaken auditability.
  - Port-level alignment keeps the business contract explicit and lets tests mirror the real
    runtime identity rules.
- **Alternatives considered**:
  - Keep the existing method signatures and ignore `architecture_version` inside the repositories:
    rejected because it preserves misleading API surface area.
  - Push the identity rewrite into MongoDB adapters only: rejected because it hides the business
    rule change below the core boundary.

### Decision 2: Detect duplicate existing identity pairs in the core via repository count methods

- **Decision**: Add a small repository query capability, such as
  `count_by_identity(micro_ag_id, environment, session)`, to both MAG repository ports and have the
  use case perform duplicate detection inside the existing transaction before any raw or processed
  upsert occurs.
- **Rationale**:
  - The duplicate-record rule is a business decision and belongs in the core orchestration layer.
  - Counting by identity through repository ports keeps MongoDB details out of the use case while
    still allowing the use case to reason over `0`, `1`, or `>1` matches.
  - Executing the count queries in the same transaction/session as the writes keeps the decision and
    the replacement path consistent.
- **Alternatives considered**:
  - Let each MongoDB repository perform its own hidden duplicate check and raise errors from the
    adapter layer: rejected because it duplicates behavior and makes created-vs-updated semantics
    harder to reason about centrally.
  - Query MongoDB directly from the use case: rejected because it would violate the hexagonal
    boundary.

### Decision 3: Represent duplicate identity conflicts as a new domain exception mapped to 409

- **Decision**: Introduce a new core exception, e.g. `DuplicateMicroAffinityGroupIdentity`, and map
  it through the existing infrastructure error pipeline to `409 Conflict` with a MAG-specific error
  code in problem-details responses.
- **Rationale**:
  - The constitution requires domain failures to be expressed as core exceptions and mapped to HTTP
    in the infrastructure layer.
  - Existing patterns such as `DuplicateDependencyEdge` and `CircularDependencyDetected` already use
    this clean split for `409 Conflict` responses.
  - A named exception makes the duplicate-state path testable at use-case, endpoint, and
    persistence-backed levels.
- **Alternatives considered**:
  - Return `422 Unprocessable Entity`: rejected because the request body can be valid while the
    stored system state is conflicting.
  - Return `500 Internal Server Error`: rejected because the conflict is deterministic and
    semantically classifiable, not an unhandled infrastructure failure.

### Decision 4: Keep full-document replacement semantics and derive created vs updated before writes

- **Decision**: Continue using full-document replacement in both MongoDB repositories, but narrow
  the `replace_one(..., upsert=True)` filter to `{micro_ag_id, environment}` and derive the
  `created` flag from the pre-upsert identity counts gathered in the use case.
- **Rationale**:
  - The clarification requires full replacement rather than merge behavior, so `replace_one` stays
    aligned with the desired semantics.
  - Deriving `created` from pre-upsert counts makes `201` vs `200` deterministic even when the new
    payload changes `architecture_version`.
  - This keeps stale fields from surviving and avoids coupling API status semantics to MongoDB’s
    `upserted_id` behavior alone.
- **Alternatives considered**:
  - Merge updates with `update_one`: rejected because it risks stale fields lingering in stored raw
    or processed documents.
  - Keep using repository return values only for created-vs-updated status: rejected because once
    duplicate detection and identity narrowing are introduced, the use case already has the cleaner
    source of truth.

### Decision 5: Treat Pydantic model changes as boundary synchronization, not field-shape redesign

- **Decision**: Preserve the current snake_case MAG field set and validation rules in the inbound
  and outbound Pydantic models, updating service-local contract wording and regenerating the models
  only if the source JSON Schema descriptions or related schema documentation need to reflect the
  new identity semantics.
- **Rationale**:
  - `architecture_version` remains required and validated exactly as before.
  - The feature changes persistence identity behavior, not the request or response field shape.
  - The generated model path is still authoritative, so any contract wording change should flow from
    `specs/001-service-skeleton/contracts/` through `generate_inbound_models.sh` rather than via
    handwritten schema edits.
- **Alternatives considered**:
  - Force structural schema changes despite unchanged payload shape: rejected because it creates
    unnecessary churn.
  - Skip schema inspection entirely: rejected because the feature specification explicitly calls for
    alignment of models and identity semantics where relevant.

### Decision 6: Synchronize fakes, seeded records, and full-suite regression around the new pair

- **Decision**: Update all MAG-specific fake repositories and MongoDB-backed assertions to use
  `(micro_ag_id, environment)` as the logical key, add explicit overwrite-with-different-version and
  duplicate-conflict tests, and finish with the required non-perf regression suite plus the core-purity check.
- **Rationale**:
  - Existing endpoint, use-case, persistence, and perf-smoke tests encode the old three-field tuple
    directly in store keys and Mongo queries.
  - The highest-risk regressions are status-code behavior, overwrite semantics, and conflict
    handling when corrupted duplicate data is seeded.
  - The user explicitly requested synchronization of fixtures, mocks, and full integration testing.
- **Alternatives considered**:
  - Update only persistence tests: rejected because endpoint and use-case fakes would continue to
    model the wrong identity.
  - Run only MAG-focused tests: rejected because the request explicitly requires the full test
    suite.

## Open Questions

None. The feature spec and clarifications are sufficient for design and task generation.