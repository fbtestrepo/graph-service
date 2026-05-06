# Research: Micro Affinity Group Submission

**Branch**: 007-add-micro-affinity-endpoint  
**Date**: 2026-05-05

## Decisions

### Decision 1: Model the endpoint contract as a feature-local JSON Schema working copy and generate the inbound Pydantic model from it

- **Decision**: Create `specs/007-add-micro-affinity-endpoint/contracts/micro_affinity_group.schema.json`
  as the planning-time request/response contract. The schema mirrors the sample payload shape,
  forbids unknown top-level and workload fields, encodes the semantic-version and exact timestamp
  rules, and requires at least one workload. Implementation should promote the finalized schema
  into `specs/001-service-skeleton/contracts/micro_affinity_group.schema.json` so
  `generate_inbound_models.sh` and the schema README remain the authoritative codegen path.
- **Rationale**:
  - Preserves the constitution’s split of responsibilities: service-local API contracts live under
    `specs/`, while only canonical/shared contracts belong under root `schemas/`.
  - Keeps the inbound Pydantic model synchronized with a schema-backed contract instead of a
    hand-maintained Python-only model.
  - Fits the repo’s existing codegen workflow and README mapping pattern.
- **Alternatives considered**:
  - Hand-write the full Pydantic model without a schema: rejected because it increases drift risk
    and breaks the repo’s spec-driven codegen pattern.
  - Add the contract under root `schemas/`: rejected because the micro affinity group payload is a
    service-specific HTTP contract, not a canonical shared schema.

### Decision 2: Keep structural validation in the inbound schema layer and move cross-collection validation into the core use case

- **Decision**: Let the inbound adapter validate JSON structure, required fields, unknown-field
  rejection, semver, exact UTC timestamp format, non-empty workloads, and duplicate workload IDs.
  Then invoke a core use case that performs repository-backed business validation against the
  `application-architectures` collection.
- **Rationale**:
  - Satisfies the constitution’s validation-first rule for JSON payloads.
  - Keeps database-backed alignment rules out of FastAPI routing code while preserving a thin
    adapter/core boundary.
  - Makes it clear which failures are schema validation (`400`/`422`) versus domain validation
    (`422` via mapped domain exceptions).
- **Alternatives considered**:
  - Perform architectural alignment checks directly in the router: rejected because it would place
    business rules in the delivery layer.
  - Push cross-collection validation into MongoDB queries only: rejected because the rule belongs
    to core orchestration and should remain testable with fake ports.

### Decision 3: Add a dedicated micro affinity group repository port and extend the application architecture repository with lookup support

- **Decision**: Introduce `MicroAffinityGroupRepository` with upsert semantics for the
  `micro-affinity-groups` collection, and extend `ApplicationArchitectureRepository` with a
  `get_by_asset_id_and_version(...)`-style lookup method so the use case can validate workloads
  through an existing adapter boundary.
- **Rationale**:
  - The feature introduces a new external persistence capability and a new external read capability,
    both of which constitutionally belong behind core ports.
  - Reusing the existing application architecture repository keeps architecture lookups isolated in
    one adapter rather than creating direct MongoDB reads elsewhere.
  - The shape matches the current repo pattern used by `UpsertComponentNode` and
    `UpsertApplicationArchitecture`.
- **Alternatives considered**:
  - Read `application-architectures` directly from the use case with `pymongo`: rejected because
    it violates core purity.
  - Create a separate lookup-only port just for service-node validation: rejected as unnecessary
    complexity because the capability naturally extends the existing repository abstraction.

### Decision 4: Validate each workload against the resolved service node using `metadata.code-repo` plus `metadata.asset-id`

- **Decision**: Treat a workload as valid only when the matching application architecture document
  contains a `service` node whose `metadata.code-repo` equals `workload.id` and whose
  `metadata.asset-id` equals `workload.asset-id`.
- **Rationale**:
  - This matches the clarified specification, which is the authoritative source for feature intent.
  - The latest clarified feature artifacts define `metadata.asset-id` as the required node field
    for validating the submitted workload `asset-id`.
  - The rule gives a concrete service-node metadata field for validating the submitted `asset-id`.
- **Alternatives considered**:
  - Validate `workload.asset-id` against `unique-id`: rejected because the latest clarified spec
    and plan now require `metadata.asset-id` for workload validation.
  - Ignore `workload.asset-id`: rejected because the spec explicitly made it a validated field.

### Decision 5: Use domain exceptions mapped to `422` for architecture lookup failures and workload mismatches

- **Decision**: Introduce explicit core exceptions for “matching application architecture not
  found” and “submitted workload does not align to a resolved service node”, and map both to
  `422 application/problem+json` through `src/infrastructure/errors/mappers.py` and
  `handlers.py`.
- **Rationale**:
  - Keeps HTTP concerns out of the core while still producing the required response semantics.
  - Aligns with the repo’s existing domain-exception mapping mechanism.
  - Makes the business rule failures easy to test directly in use-case tests.
- **Alternatives considered**:
  - Raise `HTTPException` from the use case: rejected because it leaks transport concerns into the
    core.
  - Collapse all cross-collection failures into generic validation errors in the router: rejected
    because it obscures domain intent and bypasses the global error mapping path.

### Decision 6: Mirror the repo’s current testing split: fake-repository endpoint/unit tests plus MongoDB integration tests

- **Decision**: Add three complementary test layers:
  - endpoint tests with `TestClient` and fake repositories for `201`/`200`, malformed JSON,
    semver/timestamp validation, workload lookup failure, duplicate/empty workloads, and unknown
    field rejection
  - use-case unit tests with fake repositories for cross-collection matching rules and domain
    exception behavior
  - testcontainers-backed MongoDB integration tests for upsert/overwrite semantics in the
    `micro-affinity-groups` collection
- **Rationale**:
  - Matches the existing repo testing style.
  - Separates inbound validation, core logic, and persistence semantics cleanly.
  - Satisfies the explicit user request for endpoint tests using pytest and `TestClient`/`httpx`.
- **Alternatives considered**:
  - Use only integration tests: rejected because cross-collection validation logic would be slower
    and harder to isolate.
  - Use only unit tests with no MongoDB coverage: rejected because overwrite semantics are a key
    feature requirement and need adapter-level verification.

## Open Questions

None that block Phase 1 design.