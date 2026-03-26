# HTTP API Contract (Working Copy)

**Branch**: 004-components-payload-schema  
**Date**: 2026-03-24

This contract document describes the HTTP interface relevant to this feature.

NOTE: This is a working copy for this feature. The authoritative contracts used for codegen/CI live under `specs/001-service-skeleton/contracts/`.

## Media Types

- Success responses: `application/json`
- Error responses: `application/problem+json` (RFC 7807 Problem Details)

## Standard HTTP Status Mapping

- 400: Malformed/unparseable JSON request
- 422: Validation error (schema/constraints)
- 500: Unhandled infrastructure failure (no stack trace leaked)

## Endpoints

### POST /components

Purpose: Validate and upsert a component node payload keyed by `node-id`.

- Request: `application/json` body conforming to `component_node.schema.json`
- Success responses:
  - `201 Created` when the service created a new document for `node-id`
  - `200 OK` when the service replaced an existing document for `node-id`
- Response body: the accepted component node payload
- Side effect (on success): the service persists the payload to MongoDB, replacing any existing
  document that matches the same `node-id`.
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for schema/constraint validation failures
  - `500 application/problem+json` if persistence fails for any reason

### POST /components/validate

Purpose: Verify specs-first request validation at the boundary.

- Request: `application/json` body conforming to `component.schema.json`
- Success response: `204 No Content`
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for schema/constraint validation failures

### GET /components/{component_id}

Purpose: Retrieve a component node by `node-id` (path parameter `{component_id}` is treated as `node-id`).

- Response: `200 application/json` body conforming to `component_node.schema.json`
- Error responses:
  - `404 application/problem+json` when the component does not exist
  - `500 application/problem+json` for unhandled errors (no stack trace leaked)
