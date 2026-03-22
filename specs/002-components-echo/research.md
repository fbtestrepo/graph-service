# Research: Components Echo Endpoint

**Branch**: 002-components-echo  
**Date**: 2026-03-19

## Decisions

### Decision 1: Model “arbitrary JSON” as a JSON-value root type

- **Decision**: Represent the request body and response body as an “any JSON value” type (object/array/string/number/boolean/null) at the boundary.
- **Rationale**:
  - Matches the user requirement: accept arbitrary JSON, not just objects.
  - Keeps validation at the inbound adapter boundary (per constitution).
  - Produces a stable OpenAPI/JSON Schema contract (`{}` / empty schema) with minimal drift risk.
- **Alternatives considered**:
  - **`dict[str, Any]`**: rejects arrays/primitives → violates “arbitrary JSON”.
  - **Raw request body bytes**: bypasses inbound schema validation → violates constitution.

### Decision 2: Logging behavior is truncation-only (response remains full JSON)

- **Decision**: Echo the full parsed JSON back to the client unchanged; truncate only the *log representation* to the first **4096 characters**, and indicate truncation.
- **Rationale**:
  - Truncating the HTTP response body would either (a) break JSON validity if truncated as text, or (b) require a wrapper envelope, changing semantics.
  - The explicit clarification addressed operational risk (huge payloads / secrets) for logging, not for API correctness.
- **Alternatives considered**:
  - **Truncate the response**: ambiguous for non-string JSON; likely produces invalid JSON.
  - **Wrap response** (e.g., `{ "echo": ..., "truncated": ... }`): changes contract; not requested by the spec.

> Note: If the intent is truly “response must be truncated to 4096 characters, that requires a spec + contract update to define a *new* response shape (likely an envelope with a string payload) and corresponding tests.

### Decision 3: OpenAPI 3.1 + JSON Schema 2020-12 “any JSON” contract

- **Decision**: Define an `any JSON` schema as an **empty JSON Schema** (`{}`) in `json_value.schema.json` and reference it from OpenAPI for request/response.
- **Rationale**:
  - OpenAPI 3.1 uses JSON Schema 2020-12; `{}` is a valid schema meaning “anything”.
  - Keeps contract simple and generator-friendly.
- **Alternatives considered**:
  - **`oneOf` all primitive/object/array types**: more verbose and easier to drift.
  - **Boolean schema `true`**: valid JSON Schema, but some tooling is less tolerant of boolean root schemas.

## Open Questions

None remaining that block Phase 1 design.
