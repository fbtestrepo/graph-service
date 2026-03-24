# HTTP API Contract (Working Copy)

**Branch**: 003-persist-components-payload  
**Date**: 2026-03-21

This contract document describes the HTTP interface relevant to this feature.

NOTE: This is a working copy for this feature. The authoritative contracts used for codegen/CI live under `specs/001-service-skeleton/contracts/`.

## Media Types

- Success responses: `application/json`
- Error responses: `application/problem+json` (RFC 7807 Problem Details)

## Error Model (RFC 7807)

All non-2xx responses MUST use Problem Details.

Required fields:
- `type` (string)
- `title` (string)
- `status` (integer)
- `detail` (string)

Optional fields:
- `error_code` (string)
- Validation extensions (e.g., `errors`) as needed

## Standard HTTP Status Mapping

- 400: Malformed/unparseable JSON request
- 422: Validation error (schema/constraints)
- 500: Unhandled infrastructure failure (no stack trace leaked)

## Endpoints

### GET /health

Purpose: Verify service wiring and routing works.

- Response: 200 `application/json`

### POST /components/validate

Purpose: Verify specs-first request validation at the boundary.

- Request: `application/json` body conforming to `component.schema.json`
- Success response: `204 No Content`
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for schema/constraint validation failures

### POST /components

Purpose: Accept and echo any valid JSON payload and persist it to MongoDB.

- Request: `application/json` body conforming to `json_value.schema.json` (any valid JSON value: object/array/string/number/boolean/null)
- Success response: `200 application/json` whose JSON body equals the submitted JSON value
- Side effect (on success): the service persists a new record containing:
  - `received_at` (UTC timestamp)
  - `payload` (the submitted JSON value)
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for validation failures (e.g., missing body)
  - `500 application/problem+json` if persistence fails for any reason (and MUST NOT return `200`)

Operational note: The service logs the received payload once per request; the log representation is truncated to the first 4096 characters with truncation indicated. This truncation applies to logging only; the HTTP response body is not truncated.

### GET /components/{component_id}

Purpose: Demonstrate a minimal core use case invocation and domain exception mapping.

- Response: `200 application/json` body conforming to `component.schema.json`
- Error responses:
  - `404 application/problem+json` when the component does not exist
  - `500 application/problem+json` for unhandled errors (no stack trace leaked)
