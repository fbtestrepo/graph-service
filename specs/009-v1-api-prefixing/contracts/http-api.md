# HTTP API Contract: V1 API Version Prefixing

**Branch**: 009-v1-api-prefixing  
**Date**: 2026-05-16

This contract describes the public HTTP route changes for API version prefixing.

## Media Types

- Success responses: unchanged from the current endpoint contracts
- Error responses: unchanged from the current endpoint contracts, including `application/problem+json`
  where already used

## Versioning Rule

- In-scope business routes are published under `/v1`
- `GET /health`, `/docs`, `/redoc`, and `/openapi.json` remain at the root path
- Former root business paths are not retained as the supported public contract after the feature is
  released

## Endpoint Catalog

### POST /v1/components/validate

Purpose: Validate the existing component request payload.

- Request body: unchanged existing component validation request contract
- Success response: `204 No Content`
- Error responses: unchanged from the existing contract

### POST /v1/components

Purpose: Create or replace a component document.

- Request body: unchanged existing component payload contract
- Success responses:
  - `201 Created` for a new stored record
  - `200 OK` for an overwrite of an existing record
- Response body: unchanged existing component response contract
- Error responses: unchanged from the existing contract

### GET /v1/components/{component_id}

Purpose: Retrieve a component by identifier.

- Path parameter: `component_id` unchanged in meaning
- Success response: `200 OK` with the existing component response contract
- Error responses: unchanged from the existing contract, including `404 Not Found` when applicable

### GET /v1/components/{node_id}/dependencies

Purpose: Retrieve the dependency graph for a component node.

- Path parameter: `node_id` unchanged in meaning
- Success response: `200 OK` with the existing dependency response contract
- Error responses: unchanged from the existing contract, including `404 Not Found` only when the
  root path resource is missing and `422 Unprocessable Entity` when the root exists but downstream
  graph resolution fails

### POST /v1/application-architectures

Purpose: Create or replace an application architecture document.

- Request body: unchanged existing application architecture request contract
- Success responses:
  - `201 Created` for a new stored record
  - `200 OK` for an overwrite of an existing record
- Response body: unchanged existing application architecture response contract
- Error responses: unchanged from the existing contract

### POST /v1/micro-affinity-groups

Purpose: Create or replace a processed micro affinity group document.

- Request body: unchanged existing micro affinity group request contract
- Success responses:
  - `201 Created` for a new stored record
  - `200 OK` for an overwrite of an existing record
- Response body: unchanged existing processed micro affinity group response contract
- Error responses: unchanged from the existing contract

## Root Infrastructure Routes

### GET /health

- Remains reachable at the root path
- Response contract unchanged

### GET /openapi.json

- Remains reachable at the root path
- Publishes the versioned business paths under `/v1/...`

### GET /docs

- Remains reachable at the root path
- Interactive documentation uses the root `/openapi.json` document, which describes the `/v1`
  business routes

### GET /redoc

- Remains reachable at the root path
- Displays the same root OpenAPI document with `/v1` business routes