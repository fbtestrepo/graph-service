# Data Model: Micro Affinity Group Submission

**Branch**: 007-add-micro-affinity-endpoint  
**Date**: 2026-05-05

## Overview

This feature adds `POST /micro-affinity-groups` to validate and upsert micro affinity group
documents. Structural validation occurs at the inbound boundary through a generated Pydantic v2
model derived from a feature-local JSON Schema contract. Architectural alignment validation occurs
in a core use case that consults the application architecture repository before persistence.

## Entity: MicroAffinityGroupPayload

Represents the JSON document accepted and returned by `POST /micro-affinity-groups`.

### Fields

- **`micro-ag-id`** (string, required): Primary logical identifier for the micro affinity group.
- **`name`** (string, optional): Human-readable display name.
- **`parent-asset-id`** (string, required): Asset identifier used to select the matching
  application architecture record.
- **`architecture-version`** (string, required): Semantic version for the target architecture.
- **`environment`** (string, required): Environment name participating in the uniqueness key.
- **`effective-date`** (string, required): UTC timestamp in exact `YYYY-MM-DDTHH:MM:SSZ` format.
- **`workloads`** (array, required, min length 1): List of workload entries.

### Validation Rules (Boundary)

- Root request body MUST be a JSON object.
- Unknown top-level fields are rejected.
- `name` is optional; all other top-level fields are required.
- `architecture-version` MUST match `^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$`.
- `effective-date` MUST match exact `YYYY-MM-DDTHH:MM:SSZ` form.
- `workloads` MUST contain at least one item.
- Duplicate `workload.id` values are rejected.
- Malformed JSON returns `400 application/problem+json`.
- Structural or field-format validation failures return `422 application/problem+json`.

## Entity: MicroAffinityGroupWorkload

Represents one workload entry embedded in the submitted document.

### Fields

- **`id`** (string, required): Repository identifier that must match a resolved service node’s
  `metadata.code-repo`.
- **`asset-id`** (string, required): Expected identifier for the resolved service node.

### Validation Rules

- Workload entries MUST reject unknown nested fields.
- `id` and `asset-id` are both required for every workload.
- `id` values are unique within a single request.

## Entity: ApplicationArchitectureServiceNode

Represents the subset of an application architecture node required for cross-collection
validation.

### Fields

- **`metadata.asset-id`** (string): Stable service-node asset identifier used to validate `workload.asset-id`.
- **`node-type`** (string): Must equal `service` to satisfy workload alignment.
- **`metadata.code-repo`** (string): Repository identifier used to match `workload.id`.

### Validation Rules (Core Business Validation)

- The application architecture document used for lookup is selected by
  `metadata.AssetID == parent-asset-id` and `metadata.version == architecture-version`.
- For every submitted workload, at least one resolved node MUST satisfy:
  - `node-type == "service"`
  - `metadata.code-repo == workload.id`
  - `metadata.asset-id == workload.asset-id`
- If the architecture document is missing, or any workload fails this match, the use case raises a
  domain exception that is mapped to `422`.

## Entity: MicroAffinityGroupRecord

Represents the persisted micro affinity group document stored in MongoDB.

### Collection

- **Collection**: `micro-affinity-groups`

### Identity

- Composite key: `micro-ag-id` + `environment` + `architecture-version`

### Stored Shape

- The stored MongoDB document MUST match the accepted request payload shape.
- No transport wrapper is added around the payload.

### Write Semantics

- If no record exists with the same composite key, the write creates a new record.
- If a record already exists with the same composite key, the write fully overwrites the stored
  document so removed fields do not linger.
- A different `environment` or `architecture-version` for the same `micro-ag-id` is stored as a
  separate record.

### Lifecycle / State Transitions

- **Absent -> Created**: first successful upsert for a given composite key returns `201 Created`.
- **Existing -> Overwritten**: subsequent successful upsert for the same composite key returns
  `200 OK`.
- **Parallel variants**: submissions with the same `micro-ag-id` but a different environment or
  architecture version create additional records rather than mutating the original record.

## Supporting Result Type: UpsertMicroAffinityGroupResult

Represents the core use-case result returned to the router.

### Fields

- **`created`** (boolean): `True` when MongoDB inserted a new document, `False` when the write
  overwrote an existing document.

## Notes

- The plan intentionally follows the clarified `workload.asset-id -> service node metadata.asset-id`
  rule.
- If database-level uniqueness hardening is required later, a unique compound index on
  `micro-ag-id`, `environment`, and `architecture-version` should be added as a follow-up.