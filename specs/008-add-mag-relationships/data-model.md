# Data Model: Micro Affinity Group Relationship Enrichment

**Branch**: 008-add-mag-relationships  
**Date**: 2026-05-06

## Overview

This feature keeps the existing `POST /micro-affinity-groups` request shape but changes the
successful processing pipeline into a transactional dual-write flow. A validated request is first
recorded as raw input, then transformed into an enriched document whose `relationships` field is
derived from application-architecture nodes and relationships, and finally upserted into a
processed collection.

## Entity: MicroAffinityGroupSubmission

Represents the client payload accepted by `POST /micro-affinity-groups` before any transformation.

### Fields

- **`micro-ag-id`** (string, required): Logical identifier for the micro affinity group.
- **`name`** (string, optional): Human-readable display name.
- **`parent-asset-id`** (string, required): Top-level architecture asset identifier used for every
  workload lookup.
- **`architecture-version`** (string, required): Top-level architecture version used for every
  workload lookup.
- **`environment`** (string, required): Environment participating in the record identity.
- **`effective-date`** (string, required): Exact UTC timestamp in `YYYY-MM-DDTHH:MM:SSZ` format.
- **`workloads`** (array, required, min length 1): Submitted workload members.

### Validation Rules (Boundary)

- Request body MUST remain the existing micro affinity group input contract.
- Client-supplied `relationships` is invalid input.
- Unknown top-level and nested workload fields are rejected.
- Duplicate `workload.id` values are rejected before core processing.

## Entity: MicroAffinityGroupWorkload

Represents one submitted workload entry.

### Fields

- **`id`** (string, required): Repository identifier that must match a source service node’s
  `metadata.code-repo`.
- **`asset-id`** (string, required): Service asset identifier that must match a source service
  node’s `metadata.asset-id`.

### Validation Rules

- Both fields are required.
- `id` values are unique within one submission.
- Workload entries do not contain per-workload architecture identifiers; all lookups use the
  submission’s top-level architecture selectors.

## Entity: ApplicationArchitectureServiceNode

Represents the subset of an application architecture node needed for source and destination
resolution.

### Fields

- **`unique-id`** (string): Node identifier used to join nodes to relationship edges.
- **`node-type`** (string): Must equal `service` for both source and destination resolution.
- **`metadata.code-repo`** (string): Repository identifier used to populate workload `id`.
- **`metadata.asset-id`** (string): Asset identifier used to populate workload `asset-id`.

### Validation Rules (Core Business Validation)

- Source-service lookup uses top-level `parent-asset-id` and `architecture-version` to load one
  application architecture document.
- A source node is valid only when:
  - `node-type == "service"`
  - `metadata.code-repo == submitted workload.id`
  - `metadata.asset-id == submitted workload.asset-id`
- A destination node is valid only when:
  - it is resolvable from a matched relationship edge
  - `node-type == "service"`
  - `metadata.code-repo` and `metadata.asset-id` are both present

## Entity: ApplicationArchitectureRelationshipEdge

Represents one outgoing relationship entry in the application architecture document.

### Fields

- **`relationship-type.connects.source.node`** (string): Source node `unique-id`.
- **`relationship-type.connects.destination.node`** (string): Destination node `unique-id`.

### Validation Rules

- Source matching uses the resolved source service node’s `unique-id`.
- If no edges originate from a valid source service node, processing continues for the next
  submitted workload.
- If an edge exists but the destination node cannot be resolved to a valid destination service
  workload, the submission fails with a domain error.

## Entity: RelationshipEntry

Represents one generated entry inside the transformed document’s `relationships` list.

### Fields

- **`source-workload.id`** (string): Resolved source service node `metadata.code-repo`.
- **`source-workload.asset-id`** (string): Resolved source service node `metadata.asset-id`.
- **`destination-workload.id`** (string): Resolved destination service node `metadata.code-repo`.
- **`destination-workload.asset-id`** (string): Resolved destination service node
  `metadata.asset-id`.

### Generation Rules

- One entry is generated per resolvable outgoing relationship edge.
- Destination workloads may be outside the submitted micro affinity group.
- If multiple edges point to the same destination, each edge is retained as a separate list entry.

## Entity: RawMicroAffinityGroupRecord

Represents the persisted raw input document.

### Collection

- **Collection**: `micro-affinity-groups`

### Identity

- Composite key: `micro-ag-id` + `environment` + `architecture-version`

### Write Semantics

- Successful requests upsert the raw submitted payload into this collection.
- This raw write participates in the same MongoDB transaction as transformation and processed
  upsert.
- If the transaction aborts, this raw write is rolled back.

## Entity: ProcessedMicroAffinityGroupRecord

Represents the transformed document returned by the endpoint and stored for downstream use.

### Collection

- **Collection**: `micro-affinity-groups-processed`

### Identity

- Composite key: `micro-ag-id` + `environment` + `architecture-version`

### Stored Shape

- Includes all accepted submission fields unchanged.
- Adds a required top-level `relationships` array.
- `relationships` may be empty when no outgoing relationships are discovered.

### Write Semantics

- Upserted within the same transaction as the raw write.
- Full document replacement is preferred so stale relationship entries do not linger.
- Repeated submissions for the same composite key overwrite the processed document.

### Lifecycle / State Transitions

- **Absent -> Raw + Processed Created**: first successful transaction writes both collections and
  returns `201 Created`.
- **Existing -> Raw + Processed Overwritten**: subsequent successful transaction for the same
  composite key replaces both stored representations and returns `200 OK`.
- **Failure -> Rolled Back**: any persistence or transformation failure aborts the transaction so
  neither collection reflects partial work.

## Supporting Result Type: UpsertMicroAffinityGroupResult

Represents the use-case result returned to the router.

### Fields

- **`created`** (boolean): `True` when the processed upsert created a new composite-key record,
  `False` when it replaced an existing one.
- **`payload`** (object): The stored processed document returned in the HTTP response.

## Notes

- The additive raw + processed storage model is intentional to preserve current behavior while
  adding a transformed projection.
- Transaction support requires session-aware repository operations and a replica-set-capable test
  fixture.