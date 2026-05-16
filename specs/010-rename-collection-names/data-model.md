# Data Model: Rename MongoDB Collection Names

**Branch**: 010-rename-collection-names  
**Date**: 2026-05-16

## Overview

This feature does not alter API payloads or business entities. Its design model is the internal
MongoDB collection contract used by outbound adapters and Mongo-backed persistence tests: which
collections are renamed, which references must be updated, and which invariants remain unchanged.

## Entity: CollectionNameMapping

Represents one MongoDB collection identifier that participates in the rename.

### Fields

- **`current-name`** (string, required): Existing collection name used by the service today.
- **`new-name`** (string, required): Required underscore-based replacement name.
- **`scope`** (string, required): Whether the mapping is `rename-required` or `unchanged`.
- **`consumers`** (array, required): Repositories and tests that reference the collection by name.

### Collection Mappings in Scope

- **Application Architectures**
  - `current-name`: `application-architectures`
  - `new-name`: `application_architectures`
  - `scope`: `rename-required`
- **Micro Affinity Groups Raw**
  - `current-name`: `micro-affinity-groups`
  - `new-name`: `micro_affinity_groups`
  - `scope`: `rename-required`
- **Micro Affinity Groups Processed**
  - `current-name`: `micro-affinity-groups-processed`
  - `new-name`: `micro_affinity_groups_processed`
  - `scope`: `rename-required`
- **Components**
  - `current-name`: `components`
  - `new-name`: `components`
  - `scope`: `unchanged`
- **Component Payload Records**
  - `current-name`: `component_payload_records`
  - `new-name`: `component_payload_records`
  - `scope`: `unchanged`

### Validation Rules

- Every `rename-required` collection must have exactly one underscore-based replacement.
- Every `unchanged` collection must remain untouched during implementation.
- No feature code path may continue referencing a dashed collection name after the rename is
  complete.

## Entity: PersistenceCollectionReference

Represents a hardcoded or centralized code reference to a MongoDB collection name.

### Fields

- **`file`** (string, required): Source or test file that uses the collection name.
- **`layer`** (string, required): `outbound-adapter`, `fixture`, or `persistence-test`.
- **`collection-name`** (string, required): The collection name referenced by that file.
- **`usage`** (string, required): `read`, `write`, `upsert`, `seed`, or `assert`.

### Reference Groups in Scope

- Outbound MongoDB repositories under `src/adapters/outbound/mongodb/`
- Shared Mongo-backed fixture creation in `tests/conftest.py`
- Persistence suites that call `client.app.state.mongo_db.get_collection(...)`

### Validation Rules

- All references for a renamed collection must be updated in the same implementation slice.
- References in endpoint tests that use fake repositories remain outside the rename scope unless
  they query MongoDB directly.

## Entity: StoredCollectionContract

Represents the storage invariants that must remain stable while collection identifiers change.

### Fields

- **`document-shape`** (string, required): Existing stored payload shape for the collection.
- **`indexes`** (string, required): Existing index behavior and lookup characteristics.
- **`validation-rules`** (string, required): Existing collection-level validation behavior, if any.
- **`transactional-behavior`** (string, required): Whether the collection participates in
  transactional writes.

### Validation Rules

- Collection renaming must not reshape stored documents.
- Existing query filters and uniqueness assumptions must continue to work unchanged.
- Transactional dual-write behavior for raw and processed micro affinity group collections must be
  preserved.

## Entity: TestDatabaseInteraction

Represents a persistence-backed test that seeds or verifies MongoDB state by collection name.

### Fields

- **`test-file`** (string, required): Persistence test file path.
- **`interaction-type`** (string, required): `seed`, `count`, `find-one`, `find-many`, or
  `rollback-check`.
- **`collections-used`** (array, required): MongoDB collection names touched directly in the test.

### Affected Tests

- `tests/test_application_architectures_persistence.py`
- `tests/test_micro_affinity_groups_persistence.py`
- Shared fixture path in `tests/conftest.py` (database creation only; collection names remain in
  the test files)

### Validation Rules

- Persistence tests must seed and assert against underscore-based collection names after the rename.
- Non-persistence tests that only use fake repositories should remain unchanged.

## Lifecycle / State Transitions

- **Current State**: Code and Mongo-backed persistence tests reference dashed collection names for
  application architectures and micro affinity group collections.
- **Planned State**: Code and Mongo-backed persistence tests reference underscore-based collection
  names through a centralized persistence-layer mapping.
- **Legacy Database State**: Existing dashed collections may still exist in MongoDB because the
  feature does not automatically migrate them.