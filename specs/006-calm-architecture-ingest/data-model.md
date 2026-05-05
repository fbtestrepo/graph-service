# Data Model: CALM Architecture Document Ingestion

**Branch**: 006-calm-architecture-ingest  
**Date**: 2026-05-02

## Overview

This feature adds `POST /application-architectures` to validate and upsert CALM architecture
documents. Validation occurs at the inbound boundary through a generated Pydantic v2 model rooted
in `schemas/calm/v1_2/calm.json` and constrained by a feature-specific wrapper schema. Persistence
occurs through a core repository port implemented by a MongoDB adapter.

## Entity: ApplicationArchitectureMetadata

Represents the required root metadata block that identifies an architecture record.

### Fields

- **`AssetID`** (string, required): Alphanumeric asset identifier. Regex:
  `^[a-zA-Z0-9]+$`.
- **`version`** (string, required): Semantic version identifier in `major.minor.patch` form.
  Regex: `^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$`.
- **`created`** (string, required): Calendar date in `YYYY-MM-DD` format. Must satisfy both the
  textual format and a date-aware validation step.

### Validation Rules

- The root `metadata` value MUST be a JSON object, not an array.
- All three metadata keys are mandatory.
- Additional metadata keys are allowed and preserved if the payload is otherwise valid.

## Entity: ApplicationArchitectureDocument

Represents the JSON document accepted and returned by `POST /application-architectures`.

### Core Shape

- **`metadata`** (ApplicationArchitectureMetadata, required)
- **`nodes`** (array, optional): CALM node definitions inherited from the canonical CALM schema.
- **`relationships`** (array, optional): CALM relationship definitions inherited from the
  canonical CALM schema.
- **`controls`** (object, optional): CALM controls section inherited from the canonical schema.
- **`flows`** (array, optional): CALM flow definitions inherited from the canonical schema.
- **`adrs`** (array of strings, optional): CALM ADR references inherited from the canonical
  schema.

### Validation Rules (Boundary)

- The request body root MUST be an object.
- The full payload MUST conform to the feature wrapper schema, which in turn references
  `schemas/calm/v1_2/calm.json`.
- Malformed JSON is rejected as `400 application/problem+json`.
- Schema or metadata violations are rejected as `422 application/problem+json`.

## Entity: ApplicationArchitectureRecord

Represents the persisted document stored in MongoDB.

### Collection

- **Collection**: `application-architectures`

### Identity

- Composite key: `metadata.AssetID` + `metadata.version`

### Stored Shape

- The stored MongoDB document MUST match the accepted request payload shape.
- No transport wrapper is added around the payload.

### Write Semantics

- If no document exists with the same composite key, the write creates a new record.
- If a document already exists with the same composite key, the write overwrites the stored record
  so the latest accepted payload becomes the single current representation for that asset-version
  pair.
- A different `version` for the same `AssetID` is stored as a separate record.

### Lifecycle / State Transitions

- **Absent → Created**: first successful upsert for a given `AssetID + version` returns
  `201 Created`.
- **Existing → Overwritten**: subsequent successful upsert for the same `AssetID + version`
  returns `200 OK`.
- **Parallel versions**: submissions for the same `AssetID` and a new `version` create additional
  records rather than mutating older versions.

## Supporting Result Type: UpsertApplicationArchitectureResult

Represents the core use-case result returned to the router.

### Fields

- **`created`** (boolean): `True` when MongoDB inserted a new document, `False` when the write
  overwrote an existing document.

## Notes

- A database-level unique compound index on `metadata.AssetID` and `metadata.version` is strongly
  recommended as a follow-up hardening step if it is not already provisioned.
- The core use case does not repeat JSON-schema validation; it trusts the inbound adapter to pass
  only validated payloads and focuses on identity extraction and repository orchestration.