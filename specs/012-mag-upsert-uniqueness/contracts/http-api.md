# HTTP API Contract: MAG Upsert Uniqueness

**Branch**: 012-mag-upsert-uniqueness  
**Date**: 2026-05-17

This contract documents the externally visible behavior for `POST /v1/micro-affinity-groups`
after narrowing MAG write identity to `micro_ag_id + environment`.

## Contract Scope

- Applies only to `POST /v1/micro-affinity-groups`
- Applies to request validation, success responses, and conflict behavior
- Applies to how the service interprets logical identity for raw and processed MAG writes
- Does not change route paths, request field names, response field names, or application
  architecture lookup rules

## Authoritative Sources

- Feature spec: `specs/012-mag-upsert-uniqueness/spec.md`
- Request JSON Schema source: `specs/001-service-skeleton/contracts/micro_affinity_group.schema.json`
- Response JSON Schema source:
  `specs/001-service-skeleton/contracts/micro_affinity_group_processed.schema.json`
- Generated inbound schema modules:
  - `src/adapters/inbound/api/schemas/micro_affinity_group.py`
  - `src/adapters/inbound/api/schemas/micro_affinity_group_processed.py`

## Request Contract

- The endpoint continues to accept the existing snake_case MAG payload.
- Required fields remain:
  - `micro_ag_id`
  - `parent_asset_id`
  - `architecture_version`
  - `environment`
  - `effective_date`
  - `workloads`
- `architecture_version` remains required and validated exactly as before.
- Client-supplied `relationships` remains invalid.
- Unknown fields continue to fail with the existing validation behavior.

## Identity Semantics

- The service now treats `micro_ag_id + environment` as the sole logical identity pair for MAG
  writes.
- `architecture_version` is no longer part of the write identity.
- A second request with the same `micro_ag_id + environment` but a different
  `architecture_version` is interpreted as an overwrite, not as a separate stored MAG record.
- A request with the same `micro_ag_id` and a different `environment` remains a separate MAG
  record pair.

## Success Behavior

- `201 Created`: Returned when the identity pair does not already exist and the service creates the
  raw and processed records for that pair.
- `200 OK`: Returned when the identity pair already exists and the service fully replaces the raw
  and processed records for that pair.
- Successful responses continue to return the processed MAG document and include the submitted
  `architecture_version` value.

## Conflict Behavior

- If stored data already contains more than one raw or processed record for the same
  `micro_ag_id + environment` pair, the request is rejected.
- The API returns HTTP `409 Conflict` using the existing problem-details response format.
- Implemented problem-details classification:
  - `title`: `Conflict`
  - `error_code`: `duplicate_micro_affinity_group_identity`

## Partial-State Repair Behavior

- If exactly one matching record exists in only one of the two MAG collections for an identity
  pair, the request is treated as an update rather than a conflict.
- The service completes a transactional overwrite that restores both the raw and processed pair.
- The API returns `200 OK` because the identity pair already existed before the write.

## Persistence Alignment Guarantees

- New raw writes to `micro_affinity_groups` are matched only by `micro_ag_id + environment`.
- New processed writes to `micro_affinity_groups_processed` are matched only by
  `micro_ag_id + environment`.
- Both collections continue to store `architecture_version` in the document body.
- Overwrites fully replace the stored document rather than merging new fields into older content.
- Index creation, index validation, and historical data migration remain outside the application.

## Non-Goals

- No route rename
- No payload field rename
- No programmatic MongoDB index management
- No cleanup or migration of historical duplicate data