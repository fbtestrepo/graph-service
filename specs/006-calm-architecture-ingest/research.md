# Research: CALM Architecture Document Ingestion

**Branch**: 006-calm-architecture-ingest  
**Date**: 2026-05-02

## Decisions

### Decision 1: Generate the inbound request model from a feature-specific wrapper schema rooted in CALM

- **Decision**: Create `specs/006-calm-architecture-ingest/contracts/application_architecture.schema.json`
  as the feature-local request contract. That schema references the canonical CALM entry schema
  at `schemas/calm/v1_2/calm.json` and adds the service-specific requirement that root
  `metadata` is mandatory and must contain `AssetID`, `version`, and `created`.
- **Rationale**:
  - Preserves the constitution’s split of responsibility: canonical CALM contracts remain in
    `schemas/`, while service-specific HTTP contracts remain in `specs/`.
  - Keeps Pydantic model generation specs-first and avoids hand-maintained drift.
  - Makes the user-required metadata constraints explicit in a service contract rather than hiding
    them only in Python validators.
- **Alternatives considered**:
  - Generate directly from `schemas/calm/v1_2/calm.json`: insufficient by itself because CALM’s
    root `metadata` definition allows an object or array and does not require the nested keys this
    endpoint needs.
  - Hand-write the full Pydantic model: faster initially, but higher drift risk as CALM evolves.

### Decision 2: Keep all request validation in the inbound adapter with generated Pydantic v2 models plus targeted metadata validators

- **Decision**: Extend `generate_inbound_models.sh` to generate
  `src/adapters/inbound/api/schemas/application_architecture.py` from the feature wrapper schema,
  then layer any remaining strict metadata checks in Pydantic v2 validators or companion model
  helpers inside the inbound schema module.
- **Rationale**:
  - Matches the constitution’s validation-first rule: invalid JSON never reaches the core.
  - Allows CALM-driven field structure to come from codegen while preserving exact regex/date
    behavior for `AssetID`, `version`, and `created`.
  - Reuses the repo’s existing deterministic codegen workflow and schema README mapping pattern.
- **Alternatives considered**:
  - Validate with ad hoc logic in the router: rejected because it would move business validation
    into the delivery mechanism.
  - Rely only on JSON Schema patterns: rejected because `created` should also be accepted through a
    date-aware parser check during Pydantic validation.

### Decision 3: Reuse the existing thin-router/use-case/repository pattern from POST /components

- **Decision**: Mirror the current `POST /components` flow: router accepts a generated request
  model, injects a repository port via `Depends`, calls a dataclass use case, sets `201` vs `200`
  from the use-case result, and returns the validated payload.
- **Rationale**:
  - This pattern already exists in `src/adapters/inbound/api/routers/components.py`,
    `src/core/use_cases/upsert_component_node.py`, and
    `src/adapters/outbound/mongodb/component_node_repository.py`.
  - Keeps the design simple and consistent for tests, DI wiring, and problem-details behavior.
- **Alternatives considered**:
  - Introduce a service layer outside `src/core/use_cases/`: unnecessary given the current codebase
    patterns.
  - Persist directly from the router: violates Hexagonal Architecture.

### Decision 4: Use MongoDB upsert keyed by metadata.AssetID + metadata.version and preserve full-overwrite semantics

- **Decision**: Implement persistence behind a new `ApplicationArchitectureRepository` port and a
  MongoDB adapter targeting the `application-architectures` collection. The planned write path uses
  `update_one({"metadata.AssetID": asset_id, "metadata.version": version}, {"$set": payload, ...}, upsert=True)`
  while also clearing fields omitted from the new payload so the observed behavior remains a full
  overwrite.
- **Rationale**:
  - Aligns with the user’s requested `update_one(..., {"$set": payload}, upsert=True)` plan.
  - Avoids violating the feature spec’s `FR-014` full-overwrite requirement, which bare `$set`
    would otherwise break by retaining stale optional fields.
  - Keeps create-vs-overwrite detection simple through MongoDB’s `upserted_id` result.
- **Alternatives considered**:
  - `replace_one(...)`: simpler for overwrite semantics, but it does not follow the explicit
    update-one requirement given for this planning task.
  - Plain `update_one(..., {"$set": payload}, upsert=True)` without cleanup: rejected because
    fields removed from a later payload would incorrectly remain in storage.

### Decision 5: Preserve existing HTTP classification and response semantics

- **Decision**:
  - Malformed JSON → `400 application/problem+json`
  - Schema or metadata validation failures → `422 application/problem+json`
  - New `AssetID + version` insert → `201 Created`
  - Overwrite of existing `AssetID + version` → `200 OK`
- **Rationale**:
  - Matches the constitution and the repo’s existing request validation handler in
    `src/infrastructure/errors/validation.py`.
  - Mirrors the already-tested `POST /components` success pattern and minimizes new error-mapping
    code.
- **Alternatives considered**:
  - Always return `200`: rejected because the spec explicitly distinguishes create from overwrite.
  - Add a custom response flag instead of status codes: rejected because the clarification session
    chose protocol-level differentiation.

### Decision 6: Treat the feature contracts as a working copy and defer canonical service-wide API promotion to implementation

- **Decision**: Store the feature’s OpenAPI working copy and JSON Schema wrapper under
  `specs/006-calm-architecture-ingest/contracts/` for planning and task generation. During
  implementation, the authoritative service contract set can be promoted consistently with the
  repo’s existing specs/codegen workflow.
- **Rationale**:
  - Keeps planning aligned with the current repo convention where feature folders carry working
    copies of endpoint contracts.
  - Avoids changing unrelated contract artifacts before task generation.
- **Alternatives considered**:
  - Mutate `specs/001-service-skeleton/contracts/` during planning: rejected because `/speckit.plan`
    should produce design artifacts, not implementation changes.

## Open Questions

None that block Phase 1 design.