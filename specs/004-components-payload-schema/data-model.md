# Data Model: Components Payload Validation & Upsert

**Branch**: 004-components-payload-schema  
**Date**: 2026-03-24

## Overview

This feature changes `POST /components` from “persist and echo any JSON” to “validate and upsert a component node payload keyed by `node-id`”.

Validation occurs at the inbound boundary via Pydantic models generated from JSON Schema. Persistence occurs via a core port implemented by a MongoDB outbound adapter.

## Entity: ComponentNodePayload (API request/response)

Represents the validated JSON object accepted by `POST /components`.

### Fields

- **`node-id`** (string, required, non-empty): Unique identifier for the component node.
- **`node-type`** (string, required, non-empty): Classification of the node.
- **`node-name`** (string, required, non-empty): Human-readable name.
- **`metadata`** (object, required):
  - **`parent-asset-id`** (string, required, non-empty)
  - Additional keys allowed (extensible metadata)
- **`interfaces`** (array, optional): list of interface objects
  - **`interface-local-id`** (string, required, non-empty)
  - **`interface-type`** (string, required, non-empty)
- **`relationships`** (array, optional): list of relationship objects
  - **`relationship-type`** (string, required, non-empty)
  - **`source`** (object, required):
    - **`node-id`** (string, required, non-empty)
    - **`interface-local-id`** (string, required, non-empty)
  - **`target`** (object, required):
    - **`node-id`** (string, required, non-empty)
    - **`interface-local-id`** (string, required, non-empty)

### Validation Rules (Boundary)

- Request body root MUST be an object.
- Unknown top-level keys are rejected.
- Required strings MUST have `minLength: 1`.
- If validation fails → `422 application/problem+json`.
- If JSON is malformed → `400 application/problem+json`.

## Persistence Model: ComponentNodeDocument (MongoDB)

### Collection

- **Collection**: `components`

### Stored Shape

- The stored MongoDB document MUST match the accepted payload object shape.
- The key used for upsert MUST be `node-id`.

### Write Semantics

- Insert when no existing document matches `{"node-id": <node-id>}`.
- Replace the entire document when an existing document matches `{"node-id": <node-id>}`.

### State / Lifecycle

- **Created**: first successful upsert for a given `node-id` → `201 Created`.
- **Updated**: subsequent successful upsert for the same `node-id` → `200 OK`.

## Notes

- This feature is intentionally “latest state per node-id”, not append-only audit storage.
- If a uniqueness guarantee is required at the database level, a unique index on `node-id` should be added as a follow-up.
