# HTTP API Contract: Snake Case MAG Endpoint

**Branch**: 011-snake-case-mag-api  
**Date**: 2026-05-16

This contract describes the externally visible request and success-response shape for
`POST /v1/micro-affinity-groups` after the `snake_case` migration.

## Contract Scope

- Applies only to `POST /v1/micro-affinity-groups`
- Applies to the request payload, success response payload, and newly persisted MAG documents
- Does not change the route path, status-code semantics, or application architecture payload shape
- Does not introduce backward-compatible support for kebab-case requests

## Authoritative Sources

- Sample request document: `specs/samples/micro-affinity-group/micro-affinity-group.json`
- Sample enriched response document:
  `specs/samples/micro-affinity-group/micro-affinity-group-relationships.json`
- Request JSON Schema:
  `specs/001-service-skeleton/contracts/micro_affinity_group.schema.json`
- Response JSON Schema:
  `specs/001-service-skeleton/contracts/micro_affinity_group_processed.schema.json`

## Required Field Renames

| Previous Field | New Field | Applies To |
|----------------|-----------|------------|
| `micro-ag-id` | `micro_ag_id` | Request, response, raw MongoDB write, processed MongoDB write |
| `parent-asset-id` | `parent_asset_id` | Request, response, raw MongoDB write, processed MongoDB write |
| `architecture-version` | `architecture_version` | Request, response, raw MongoDB write, processed MongoDB write |
| `effective-date` | `effective_date` | Request, response, raw MongoDB write, processed MongoDB write |
| `asset-id` | `asset_id` | Request workloads, response workloads, generated relationships, persisted documents |
| `source-workload` | `source_workload` | Success response, processed MongoDB write |
| `destination-workload` | `destination_workload` | Success response, processed MongoDB write |

## Request Contract

- The endpoint accepts only `snake_case` keys documented in the request schema.
- `relationships` remains server-generated and is invalid if supplied by the client.
- Unknown top-level or nested fields are rejected with the existing validation error semantics.

### Required Top-Level Request Fields

- `micro_ag_id`
- `parent_asset_id`
- `architecture_version`
- `environment`
- `effective_date`
- `workloads`

### Required Workload Fields

- `id`
- `asset_id`

## Success Response Contract

- Successful responses return `snake_case` keys only.
- The response echoes the accepted request fields and adds `relationships`.
- Each relationship entry contains `source_workload` and `destination_workload` objects.

## Persistence Alignment Guarantees

- New raw MAG documents in `micro_affinity_groups` use the request contract field names exactly.
- New processed MAG documents in `micro_affinity_groups_processed` use the response contract field
  names exactly.
- No compatibility writes are made to historical kebab-case document shapes.

## Verified Implementation Notes

- Legacy kebab-case MAG request bodies now fail validation with the existing `422` problem-details
  behavior; they are no longer accepted through alias translation.
- The implemented router, use case, mapper, and MongoDB repositories now exchange and persist MAG
  payloads using native `snake_case` keys only.
- Verification completed on 2026-05-16 with:
  - Focused MAG regression suite: `31 passed`
  - Optional MAG perf-smoke suite: `1 passed`
  - Required non-perf functional regression suite: `82 passed`, `3 deselected`

## Non-Goals

- No route rename or path-prefix change
- No automatic migration of historical MongoDB documents
- No dual-format request acceptance for kebab-case and snake_case
