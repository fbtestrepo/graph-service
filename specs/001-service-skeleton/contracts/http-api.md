# HTTP API Contract (Scaffold)

**Branch**: 001-service-skeleton  
**Date**: 2026-03-14

This contract document describes the minimal HTTP interface required for the architectural skeleton.
It is intentionally small and exists to validate repository structure, routing, and error handling.

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

- 400: Malformed business request
- 401: LDAP authentication failed
- 403: LDAP authorization failed
- 404: Node/dependency not found
- 409: State conflict (duplicate edge)
- 422: Validation error (schema/constraints)
- 500: Unhandled infrastructure failure (no stack trace leaked)

## Endpoints

### GET /health

Purpose: Verify service wiring and routing works.

- Response: 200 `application/json`

Example response:

```json
{
  "status": "ok",
  "service": "dependency-graph-service",
  "version": "dev",
  "time": "2026-03-14T12:34:56Z"
}
```

### POST /components/validate

Purpose: Verify specs-first request validation at the boundary.

- Request: `application/json` body conforming to `component.schema.json`
- Success response: `204 No Content`
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for schema/constraint validation failures

### POST /components

Purpose: Validate and upsert a component node payload keyed by `node-id`.

- Request: `application/json` body conforming to `component_node.schema.json`
- Success responses:
  - `201 Created` when the service created a new document for `node-id`
  - `200 OK` when the service replaced an existing document for `node-id`
- Response body: the accepted component node payload
- Side effect (on success): The service persists the payload to MongoDB, replacing any existing document that matches the same `node-id`.
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for schema/constraint validation failures
  - `500 application/problem+json` when persistence fails for any reason (no `200` is returned)

### GET /components/{component_id}

Purpose: Retrieve a component node by `node-id` (path parameter `{component_id}` is treated as `node-id`).

- Response: `200 application/json` body conforming to `component_node.schema.json`
- Error responses:
  - `404 application/problem+json` when the component does not exist
  - `500 application/problem+json` for unhandled errors (no stack trace leaked)

