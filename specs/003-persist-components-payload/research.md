# Research: Persist Components Payload

**Branch**: 003-persist-components-payload  
**Date**: 2026-03-21

## Decisions

### Decision 1: Persist arbitrary JSON as a field value inside a MongoDB document

- **Decision**: Store each received JSON value under a stable document shape:
  - `received_at` (UTC timestamp)
  - `payload` (the parsed JSON value; may be object/array/string/number/boolean/null)
- **Rationale**:
  - MongoDB documents must be objects; wrapping the JSON value in a `payload` field supports all JSON root types.
  - The boundary already parses JSON via Pydantic; persistence should store the parsed value, not raw bytes.
- **Alternatives considered**:
  - Store raw JSON string only: loses type fidelity (numbers/booleans/null) and makes querying harder.
  - Restrict to objects only: violates the existing “any JSON value” contract.

### Decision 2: Persist via a core port + use case (not from the inbound router)

- **Decision**: Introduce a new core port (repository interface) for persisting payload records, and a core use case that coordinates persistence and echo behavior.
- **Rationale**:
  - Preserves hexagonal architecture: inbound adapter stays thin; MongoDB details stay in outbound adapter.
  - Keeps `src/core/` testable with an in-memory/fake port.
- **Alternatives considered**:
  - Write to MongoDB directly from the FastAPI router: violates the constitution’s “external integrations are adapters” rule.

### Decision 3: Explicit 500 Problem Details on persistence failures

- **Decision**: If persistence fails, return `500 application/problem+json` (standard RFC7807 response) and do not return `200`.
- **Rationale**:
  - Prevents false success.
  - Matches constitution guidance: infrastructure failures are `500` and are mapped centrally without leaking stack traces.
- **Alternatives considered**:
  - Still return `200` and log failure: unacceptable because persistence is a feature requirement.

### Decision 4: Integration tests run MongoDB locally using testcontainers (Docker)

- **Decision**: Use a pytest fixture to run a local MongoDB via Docker/testcontainers for integration tests, and point the app at that MongoDB URI.
- **Rationale**:
  - Real persistence validation (no mocks) and repeatable local setup.
  - Matches the requirement to “run mongodb locally” for tests.
- **Alternatives considered**:
  - `mongomock`: faster but not a real MongoDB server (can hide BSON/driver differences).
  - Require developers to install and run `mongod` manually: works, but is less repeatable and harder for CI.

## Open Questions

None remaining that block Phase 1 design.
