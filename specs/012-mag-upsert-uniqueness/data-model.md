# Data Model: MAG Upsert Uniqueness

**Branch**: 012-mag-upsert-uniqueness  
**Date**: 2026-05-17

## Overview

This feature keeps the existing `POST /v1/micro-affinity-groups` request and response field shape
but changes the logical persistence identity for both raw and processed Micro-AG documents from a
three-field tuple to the pair `micro_ag_id + environment`. `architecture_version` remains required
input and continues to drive application-architecture enrichment, but it no longer partitions
stored MAG records.

## Entity: MicroAffinityGroupSubmission

Represents the client payload accepted by `POST /v1/micro-affinity-groups`.

### Fields

- **`micro_ag_id`** (string, required): Logical identifier for the micro affinity group.
- **`name`** (string, optional): Human-readable label for the group.
- **`parent_asset_id`** (string, required): Asset identifier used to locate the application
  architecture.
- **`architecture_version`** (string, required): Semantic version used for architecture lookup and
  echoed in stored raw and processed documents.
- **`environment`** (string, required): Environment boundary that participates in record identity.
- **`effective_date`** (string, required): UTC timestamp in `YYYY-MM-DDTHH:MM:SSZ` format.
- **`workloads`** (array, required, min length 1): Workload members submitted by the client.

### Validation Rules

- All fields remain snake_case.
- `architecture_version` remains required and keeps its existing semantic-version validation.
- `micro_ag_id` and `environment` remain required and are the logical identity pair for writes.
- Duplicate `workloads[].id` values remain invalid before the payload reaches the core.
- Client-supplied `relationships` remains invalid input.

## Entity: MicroAffinityGroupIdentityPair

Represents the narrowed application-side identity for MAG writes.

### Fields

- **`micro_ag_id`** (string): Logical group identifier.
- **`environment`** (string): Environment namespace for that group.

### Rules

- At most one raw record and one processed record should exist for a given pair.
- A new submission with the same pair fully replaces both stored documents, even if
  `architecture_version` changed.
- A new submission with the same `micro_ag_id` but a different `environment` creates a distinct
  record pair.
- If more than one raw or processed record already exists for the pair, the write fails with a
  conflict instead of choosing an arbitrary winner.

## Entity: MicroAffinityGroupWorkload

Represents one submitted workload entry.

### Fields

- **`id`** (string, required): Repository or workload identifier matched to a source service node.
- **`asset_id`** (string, required): Service asset identifier matched to a source service node.

### Validation Rules

- Both fields remain required.
- `id` values are unique within one submission.
- Workloads do not carry their own architecture version; enrichment continues to use the
  submission-level `parent_asset_id` and `architecture_version`.

## Entity: RelationshipEntry

Represents one generated processed relationship.

### Fields

- **`source_workload.id`** (string, required)
- **`source_workload.asset_id`** (string, required)
- **`destination_workload.id`** (string, required)
- **`destination_workload.asset_id`** (string, required)

### Generation Rules

- Derived from the application architecture located by `parent_asset_id + architecture_version`.
- Present only in the processed document and the success response.
- May be an empty list if no resolvable outgoing relationships exist.

## Entity: RawMicroAffinityGroupRecord

Represents the raw submission stored in MongoDB.

### Collection

- **Collection**: `micro_affinity_groups`

### Identity

- Logical identity: `micro_ag_id + environment`

### Stored Shape

- Mirrors the validated request payload.
- Retains `architecture_version` as a regular stored field.
- Does not contain `relationships`.

### Write Semantics

- First write for a pair inserts the document.
- Later write for the same pair fully replaces the document.
- Duplicate pre-existing documents for the pair cause the request to fail with conflict.

## Entity: ProcessedMicroAffinityGroupRecord

Represents the enriched record stored for downstream consumption and returned by the endpoint.

### Collection

- **Collection**: `micro_affinity_groups_processed`

### Identity

- Logical identity: `micro_ag_id + environment`

### Stored Shape

- Includes the full request payload fields.
- Retains `architecture_version` as a regular stored field.
- Adds generated `relationships`.

### Write Semantics

- Written in the same transaction as the raw record.
- Fully replaced on subsequent writes for the same identity pair.
- Duplicate pre-existing documents for the pair cause the request to fail with conflict.

## Supporting Entity: DuplicateMicroAffinityGroupIdentity

Represents the business conflict raised when stored data already violates the new identity rule.

### Context Fields

- **`micro_ag_id`** (string)
- **`environment`** (string)

### Behavior

- Triggered when either the raw or processed repository reports more than one existing record for
  the identity pair.
- Mapped to HTTP `409 Conflict` through the infrastructure error layer.

## Supporting Result Type: UpsertMicroAffinityGroupResult

Represents the use-case result returned to the router.

### Fields

- **`created`** (boolean): `True` only when the identity pair was absent before the write and both
  raw and processed documents were newly created for that pair.
- **`payload`** (object): The processed document returned by the endpoint.

## Lifecycle / State Transitions

- **Absent -> Created**: No raw or processed record exists for the pair. Successful request writes
  both collections and returns `201 Created`.
- **Existing Pair -> Replaced**: One raw and one processed record exist for the pair. Successful
  request fully replaces both and returns `200 OK`, even if `architecture_version` changed.
- **Different Environment -> Coexists**: Same `micro_ag_id` submitted for a different environment
  creates a distinct pair and returns `201 Created`.
- **Duplicate Existing Pair -> Conflict**: More than one raw or processed record exists for the
  pair. Request fails with `409 Conflict` and neither collection is modified.
- **Partial Existing Pair -> Repaired**: If exactly one collection contains one matching record and
  the other does not, a successful request repairs the pair transactionally and returns `200 OK`.
- **Failure During Write -> Rolled Back**: Any enrichment or persistence failure aborts the
  transaction so neither collection reflects a partial update.