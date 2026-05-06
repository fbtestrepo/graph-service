# HTTP API Contract (Working Copy)

**Branch**: 007-add-micro-affinity-endpoint  
**Date**: 2026-05-05

This contract document describes the HTTP interface relevant to the micro affinity group
submission feature.

## Media Types

- Success responses: `application/json`
- Error responses: `application/problem+json` (RFC 7807 Problem Details)

## Standard HTTP Status Mapping

- `400`: Malformed/unparseable JSON request
- `422`: Validation error (schema, field-format, or cross-collection workload alignment failure)
- `500`: Unhandled infrastructure failure (no stack trace leaked)

## Endpoints

### POST /micro-affinity-groups

Purpose: Validate and upsert a micro affinity group document keyed by `micro-ag-id` +
`environment` + `architecture-version`.

- Request: `application/json` body conforming to `micro_affinity_group.schema.json`
- Success responses:
  - `201 Created` when the service creates a new record for the supplied unique key
  - `200 OK` when the service overwrites an existing record for the supplied unique key
- Response body: the stored micro affinity group document
- Side effect (on success): the service persists the payload into MongoDB collection
  `micro-affinity-groups`
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for request-schema or cross-collection validation failures
  - `500 application/problem+json` if persistence fails for any reason

## Contract Notes

- `micro_affinity_group.schema.json` is a planning-time working copy of the service contract.
- The authoritative implementation-time codegen source is expected to live under
  `specs/001-service-skeleton/contracts/` so the existing `generate_inbound_models.sh` workflow
  remains intact.
- The request contract is closed: unknown top-level and workload fields are rejected.
- JSON Schema captures field presence and format rules; duplicate workload IDs and architecture
  lookup alignment are enforced in Python validation/use-case logic.
- The endpoint distinguishes create vs overwrite using HTTP status codes rather than an extra
  response flag.