NOTE: This document is a mirror only. The authoritative contract set for CI/codegen is in specs/001-service-skeleton/contracts/.
## Media Types

- Success responses: `application/json`
- Error responses: `application/problem+json` (RFC 7807 Problem Details)

## Endpoint

### POST /components

Purpose: Accept any valid JSON request body and return the same JSON in the response.

- Request: `application/json` with body schema `json_value.schema.json` (free-form JSON)
- Success response: `200 OK` with `application/json` body schema `json_value.schema.json`
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for validation errors (e.g., missing body)

Operational note:
- The server logs the received payload once per request, truncating the *log representation* to the first 4096 characters and indicating truncation.
