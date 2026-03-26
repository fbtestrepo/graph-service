# Research: Components Payload Validation Schema

**Branch**: 004-components-payload-schema  
**Date**: 2026-03-24

## Decisions

### Decision 1: Keep the existing HTTP error classification for JSON parsing vs validation

- **Decision**:
  - Malformed/unparseable JSON → `400 application/problem+json`
  - Schema/constraint validation errors (missing required fields, empty strings, wrong types, unknown top-level fields) → `422 application/problem+json`
- **Rationale**:
  - The service already centralizes validation error handling in `src/infrastructure/errors/validation.py`.
  - Matches the project constitution and existing tests (`/components` and `/components/validate`).
- **Alternatives considered**:
  - Return `400` for missing required fields: conflicts with the constitution and current validation handler.

### Decision 2: Introduce a dedicated JSON Schema for the `/components` upsert payload


- **Decision**: Add a new JSON Schema (Draft 2020-12) for the component node payload, based on the sample document.
- **Rationale**:
  - Prevents overloading the existing `component.schema.json` (used by `/components/validate`).
  - Makes the `/components` contract explicit for both upsert and retrieval: required `node-id`, `node-type`, `node-name`, and `metadata.parent-asset-id`; optional `interfaces` and `relationships` (returned by `GET /components/{component_id}` where `{component_id}` is treated as `node-id`).
- **Alternatives considered**:
  - Replacing `component.schema.json` with the new shape: would create broad API and domain ripple effects.

### Decision 3: Strict top-level validation with flexible `metadata`

- **Decision**:
  - Forbid unknown top-level properties (`additionalProperties: false`).
  - Allow extra keys under `metadata` (`metadata.additionalProperties: true`).
- **Rationale**:
  - Enforces a stable API surface.
  - Keeps `metadata` extensible without frequent contract updates.
- **Alternatives considered**:
  - Allow unknown top-level fields: makes contract drift likely and reduces safety.

### Decision 4: Generate the Pydantic model from JSON Schema

- **Decision**: Generate a Pydantic v2 model in `src/adapters/inbound/api/schemas/` from the authoritative JSON Schema in `specs/001-service-skeleton/contracts/` using `datamodel-code-generator`.
- **Rationale**:
  - Maintains “specs-first” and avoids hand-written schema drift.
  - Handles hyphenated JSON keys via Pydantic aliases (e.g., `node-id`).
- **Alternatives considered**:
  - Hand-written Pydantic models: faster initially but higher drift risk.

### Decision 5: MongoDB persistence uses upsert-by-`node-id` and full document replacement

- **Decision**: Persist the component payload in MongoDB using `replace_one(filter={"node-id": node_id}, replacement=payload, upsert=True)`.
- **Rationale**:
  - Directly matches the requirement “if there is already document with the same node-id stored… replace/update that document with the new json payload”.
  - Keeps the stored document shape identical to the accepted payload (no wrapper required).
- **Alternatives considered**:
  - `update_one(..., {"$set": payload}, upsert=True)`: does not remove fields omitted in the new payload.
  - Append-only audit records (`insert_one`): does not implement replacement semantics.

### Decision 6: Determine `201` vs `200` from the upsert result

- **Decision**: Treat `upserted_id != None` as “created” (`201`); otherwise “updated” (`200`).
- **Rationale**:
  - Derived directly from MongoDB driver return values; no extra read required.
- **Alternatives considered**:
  - Pre-read to check existence: adds an extra round trip and race window.

## Open Questions

None that block Phase 1 design.
