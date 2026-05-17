# Data Model: Snake Case MAG API

**Branch**: 011-snake-case-mag-api  
**Date**: 2026-05-16

## Overview

This feature keeps the existing `/v1/micro-affinity-groups` use case and persistence flow but
changes the request, response, and new-write document shape from kebab-case to `snake_case`.
The key business behavior remains the same: a validated submission is stored as a raw record,
transformed into a relationship-enriched projection, and upserted into the processed collection.

## Entity: MicroAffinityGroupSubmission

Represents the client payload accepted by `POST /v1/micro-affinity-groups`.

### Fields

- **`micro_ag_id`** (string, required): Logical identifier for the micro affinity group.
- **`name`** (string, optional): Human-readable display name.
- **`parent_asset_id`** (string, required): Top-level architecture asset identifier used for the
  application architecture lookup.
- **`architecture_version`** (string, required): Semantic version used for the application
  architecture lookup and record identity.
- **`environment`** (string, required): Environment participating in the record identity.
- **`effective_date`** (string, required): Exact UTC timestamp in `YYYY-MM-DDTHH:MM:SSZ` format.
- **`workloads`** (array, required, min length 1): Submitted workload members.

### Validation Rules (Boundary)

- Request bodies MUST use the documented `snake_case` field names only.
- Client-supplied `relationships` is invalid input.
- Unknown top-level and nested workload fields are rejected.
- Duplicate `workloads[].id` values are rejected before core processing.

## Entity: MicroAffinityGroupWorkload

Represents one submitted workload entry.

### Fields

- **`id`** (string, required): Repository identifier that must match a source service node’s
  `metadata.code-repo`.
- **`asset_id`** (string, required): Service asset identifier that must match a source service
  node’s `metadata.asset-id`.

### Validation Rules

- Both fields are required.
- `id` values are unique within one submission.
- Workload entries do not contain per-workload architecture selectors; all lookups use the
  submission’s top-level `parent_asset_id` and `architecture_version`.

## Entity: RelationshipEntry

Represents one server-generated relationship entry inside the transformed document.

### Fields

- **`source_workload.id`** (string, required): Resolved source service node repository identifier.
- **`source_workload.asset_id`** (string, required): Resolved source service node asset identifier.
- **`destination_workload.id`** (string, required): Resolved destination service node repository
  identifier.
- **`destination_workload.asset_id`** (string, required): Resolved destination service node asset
  identifier.

### Generation Rules

- One entry is generated per resolvable outgoing application architecture relationship.
- Destination workloads may be outside the submitted MAG membership.
- `relationships` may be an empty list when no outgoing relationships are found.

## Entity: ApplicationArchitectureReference

Represents the read-only architecture document shape consumed during enrichment.

### Fields Used by This Feature

- **`metadata.AssetID`** and **`metadata.version`**: Used to select the architecture document.
- **`nodes[].unique-id`** and **`nodes[].node-type`**: Used for source and destination node
  resolution.
- **`nodes[].metadata.code-repo`** and **`nodes[].metadata.asset-id`**: Used to match workloads and
  construct generated relationship workloads.
- **`relationships[].relationship-type.connects.source.node`** and
  **`relationships[].relationship-type.connects.destination.node`**: Used to traverse edges.

### Notes

- This feature does not rename application architecture field names.
- The MAG rename affects only the MAG request, response, and new MongoDB write shape.

## Entity: RawMicroAffinityGroupRecord

Represents the persisted raw submission written to MongoDB.

### Collection

- **Collection**: `micro_affinity_groups`

### Identity

- Composite key: `micro_ag_id` + `environment` + `architecture_version`

### Stored Shape

- Mirrors the validated request payload exactly, using `snake_case` keys only.
- Does not include `relationships`.

### Write Semantics

- Successful requests upsert the raw submitted payload into this collection.
- Only snake_case documents written by the new endpoint behavior are matched and overwritten.
- Historical kebab-case documents remain in storage and are not migrated or rewritten.

## Entity: ProcessedMicroAffinityGroupRecord

Represents the enriched document returned by the endpoint and stored for downstream use.

### Collection

- **Collection**: `micro_affinity_groups_processed`

### Identity

- Composite key: `micro_ag_id` + `environment` + `architecture_version`

### Stored Shape

- Includes all accepted submission fields using `snake_case` keys.
- Adds a required top-level `relationships` array of `RelationshipEntry` objects.

### Write Semantics

- Upserted within the same transaction as the raw write.
- Full document replacement is preferred so stale relationship entries do not linger.
- Repeated snake_case submissions for the same composite key overwrite the processed document.

## Supporting Result Type: UpsertMicroAffinityGroupResult

Represents the use-case result returned to the router.

### Fields

- **`created`** (boolean): `True` when the processed upsert created a new composite-key record,
  `False` when it replaced an existing snake_case record.
- **`payload`** (object): The processed MAG document returned in the HTTP response.

## Lifecycle / State Transitions

- **Absent -> Raw + Processed Created**: First successful snake_case submission writes both
  collections and returns `201 Created`.
- **Existing Snake Case -> Raw + Processed Overwritten**: Subsequent successful snake_case
  submission for the same composite key replaces both stored representations and returns `200 OK`.
- **Existing Historical Kebab Case -> Historical Record Left Untouched**: A legacy kebab-case
  document with the same logical identity is outside migration scope and is not rewritten by this
  feature.
- **Failure -> Rolled Back**: Any persistence or enrichment failure aborts the transaction so
  neither collection reflects a partial update.
