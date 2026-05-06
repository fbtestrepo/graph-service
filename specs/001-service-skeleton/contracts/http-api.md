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

### POST /application-architectures

Purpose: Validate and upsert a CALM application architecture document keyed by
`metadata.AssetID` + `metadata.version`.

- Request: `application/json` body conforming to `application_architecture.schema.json`
- Success responses:
  - `201 Created` when the service creates a new record for the supplied `AssetID` and `version`
  - `200 OK` when the service overwrites an existing record for the supplied `AssetID` and
    `version`
- Response body: the stored application architecture document
- Side effect (on success): The service persists the payload to MongoDB collection
  `application-architectures`, overwriting any existing document that matches the same
  `AssetID + version` pair.
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for CALM schema or metadata validation failures
  - `500 application/problem+json` when persistence fails for any reason

### POST /micro-affinity-groups

Purpose: Validate and upsert a micro affinity group document keyed by `micro-ag-id` +
`environment` + `architecture-version`.

- Request: `application/json` body conforming to `micro_affinity_group.schema.json`
- Success responses:
  - `201 Created` when the service creates a new record for the supplied unique key
  - `200 OK` when the service overwrites an existing record for the supplied unique key
- Response body: the stored micro affinity group document
- Side effect (on success): The service persists the payload to MongoDB collection
  `micro-affinity-groups`, overwriting any existing document that matches the same
  `micro-ag-id + environment + architecture-version` tuple.
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for request-schema, field-format, or cross-collection
    validation failures
  - `500 application/problem+json` when persistence fails for any reason

### GET /components/{component_id}

Purpose: Retrieve a component node by `node-id` (path parameter `{component_id}` is treated as `node-id`).

- Response: `200 application/json` body conforming to `component_node.schema.json`
- Error responses:
  - `404 application/problem+json` when the component does not exist
  - `500 application/problem+json` for unhandled errors (no stack trace leaked)

### GET /components/{node_id}/dependencies

Purpose: Retrieve the full transitive dependency graph (upstream + downstream) for a root component node.

Semantics:

- The response includes **both** downstream and upstream reachability.
  - Downstream traversal follows edges `source-node-id → target-node-id`.
  - Upstream traversal follows edges in reverse direction (`target-node-id → source-node-id`).
- Traversal expands **one hop at a time** (level-order) and is capped at **20 hops** from the root.
- Boundary rule at depth 20: the service may fetch/include edges incident to depth-20 nodes only when both endpoints are already within ≤ 20 hops from the root; it must not include edges that would introduce hop-21 nodes, and must not expand beyond depth 20.
- Edge extraction rule: edges are derived from stored component-node relationship records, and only “self-sourced” relationships are included (i.e., only include relationships where `relationship.source.node-id == document.node-id`).
- Cycles: the service must avoid infinite loops and may include cycle-closing edges.
- The returned edge list is **deduplicated** and **deterministically ordered** by: `relationship-type`, then `source-node-id`, then `target-node-id` (ascending lexical order).
- Missing-node edges (FR-011 intent): if an edge references a node-id that does not exist as a stored component node, the edge is still included; indirect expansion beyond missing nodes is not required.

- Response: `200 application/json` body conforming to `component_dependencies_response.schema.json`
- Error responses:
  - `404 application/problem+json` when the root node does not exist
  - `500 application/problem+json` for unhandled errors (no stack trace leaked)

