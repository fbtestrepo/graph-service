# Research: Snake Case MAG API

**Branch**: 011-snake-case-mag-api  
**Date**: 2026-05-16

## Decisions

### Decision 1: Treat the MAG JSON Schemas and sample documents under `specs/` as the contract source of truth

- **Decision**: Start the migration by updating the MAG sample documents in
  `specs/samples/micro-affinity-group/` and the generated-model source schemas in
  `specs/001-service-skeleton/contracts/` so every documented MAG request/response field becomes
  native `snake_case`.
- **Rationale**:
  - Repository conventions place service-level endpoint contracts under `specs/`, not root
    `schemas/`, and `generate_inbound_models.sh` reads the MAG JSON Schemas from
    `specs/001-service-skeleton/contracts/`.
  - Starting at those files prevents contract drift between sample documents, JSON Schema, and
    generated Pydantic models.
  - This matches the constitution split between feature/service specs and shared canonical
    contracts.
- **Alternatives considered**:
  - Hand-edit generated Pydantic models only: rejected because regeneration would reintroduce drift.
  - Treat root `schemas/` as the migration entry point: rejected because the MAG endpoint contracts
    are not stored there today.

### Decision 2: Regenerate the inbound MAG models and preserve the custom post-generation validator

- **Decision**: Use the existing `generate_inbound_models.sh` workflow after the JSON Schema update,
  keeping the script’s MAG-specific post-processing that renames the generated base class to
  `MicroAffinityGroupDocument` and appends the unique-workload-id validator subclass.
- **Rationale**:
  - The script already generates both MAG schema modules and applies the custom wrapper logic for
    `MicroAffinityGroup` after code generation.
  - The post-generation logic is class-name based, so it remains valid when field names switch to
    `snake_case`.
  - Reusing the current codegen path is the cleanest way to remove `Field(alias=...)` usage rather
    than manually rewriting generated files.
- **Alternatives considered**:
  - Manually rewrite `src/adapters/inbound/api/schemas/micro_affinity_group.py` and
    `micro_affinity_group_processed.py`: rejected because the files are generated artifacts.
  - Add a separate handwritten snake_case schema module: rejected because it would duplicate the
    codegen contract path and complicate review.

### Decision 3: Remove alias-driven serialization and run MAG payloads as native `snake_case` dictionaries end-to-end

- **Decision**: Update the MAG router to pass native `snake_case` dictionaries into the use case,
  and let the regenerated response model emit `snake_case` JSON without `by_alias=True` or alias
  fields.
- **Rationale**:
  - The current router explicitly converts inbound models back to kebab-case with
    `payload.model_dump(by_alias=True, ...)`, which is the main adapter-level translation point.
  - Native `snake_case` dicts remove friction in Python field access and eliminate the need for
    alias translation in both request handling and response serialization.
  - This is the smallest architectural change that satisfies the requested public contract change.
- **Alternatives considered**:
  - Keep aliases and merely accept both styles: rejected because the feature explicitly removes
    kebab-case alias reliance.
  - Add a compatibility translation layer inside the router: rejected because it preserves the old
    behavior instead of removing it.

### Decision 4: Update only the MAG-specific dict-key consumers in core and MongoDB adapters

- **Decision**: Limit implementation changes to the existing MAG field-name consumers:
  `src/core/use_cases/upsert_micro_affinity_group.py`,
  `src/core/domain/micro_affinity_group_relationship_mapper.py`,
  `src/adapters/outbound/mongodb/micro_affinity_group_repository.py`, and
  `src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py`.
- **Rationale**:
  - Those files are the only runtime components that currently depend on kebab-case MAG payload
    keys or use those keys in MongoDB query filters.
  - The application architecture document format remains unchanged and continues to use its current
    field names; only the MAG request/response/persistence shape changes.
  - A narrow file set keeps the review focused and preserves the existing clean-architecture split.
- **Alternatives considered**:
  - Introduce a generic key-conversion utility across the application: rejected because the change
    is feature-specific and would add unnecessary abstraction.
  - Rewrite unrelated endpoints or shared abstractions for naming consistency: rejected because the
    spec scopes the change to `/v1/micro-affinity-groups` only.

### Decision 5: Keep historical kebab-case MongoDB documents untouched and avoid dual-read or dual-write behavior

- **Decision**: New MAG writes use `snake_case` keys only, and repository upserts match on
  `snake_case` identity fields only. Existing historical kebab-case documents remain untouched in
  storage and are not rewritten or matched through compatibility queries.
- **Rationale**:
  - The feature explicitly excludes migration of historical MongoDB documents.
  - Avoiding dual-format query logic keeps persistence behavior straightforward and reviewable.
  - This prevents the feature from expanding into a data-migration or backward-compatibility layer.
- **Alternatives considered**:
  - Dual-read or dual-write support across kebab-case and snake_case documents: rejected because it
    increases runtime complexity and conflicts with the requested clean migration.
  - Automatic migration of historical documents: rejected as out of scope.

### Decision 6: Synchronize MAG-focused fixtures and then prove safety with the non-perf functional regression suite

- **Decision**: Update the MAG endpoint, mapper, use-case, persistence, and perf-smoke fixtures to
  `snake_case`, then run the repository’s required functional regression gate
  `python -m pytest tests -v -k "not perf_smoke"` to prove no unrelated regressions.
- **Rationale**:
  - MAG field-name assertions are concentrated in a small set of MAG-specific tests, so the test
    surface can be updated mechanically without broad repo churn.
  - The user explicitly requested test-suite synchronization and functional regression execution.
  - The non-perf suite exercises both isolated and MongoDB-backed behavior without relying on the
    optional perf smoke tests.
- **Alternatives considered**:
  - Update only endpoint tests: rejected because persistence, mapper, and use-case assertions also
    encode the old key shape.
  - Run only MAG-focused suites: rejected because the user asked for all functional tests.

## Open Questions

None. The contract authority, compatibility stance, and regression strategy are sufficiently
resolved for implementation planning.