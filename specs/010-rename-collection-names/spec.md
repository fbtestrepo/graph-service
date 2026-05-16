# Feature Specification: Rename MongoDB Collection Names

**Feature Branch**: `010-rename-collection-names`  
**Created**: 2026-05-16  
**Status**: Draft  
**Input**: User description: "Rename MongoDB collection names to use underscores instead of dashes.

Problem Statement
Current MongoDB collection names use dashes (kebab-case), which deviates from Python/FastAPI backend best practices.

Requirements
1. Naming Convention: Rename all database collections from `kebab-case` (dashes) to lowercase `snake_case` (underscores).
  - Example: `micro-affinity-groups` rename to `micro_affinity_groups`

2. Code Alignment: Update all repository-layer collection references, Mongo-backed persistence test assertions, and direct database verification code that reference renamed collections so they match the new names exactly.

3. Data Integrity: The document structures and repository-observable persistence behavior associated with the renamed collections must remain unchanged. Any required indexes or validation rules on the underscore-based collections are provisioned outside this feature.

Out of Scope
- Modifying REST API endpoint paths, Pydantic model fields, or core business logic."

## Clarifications

### Session 2026-05-16

- Q: How should existing dashed collections be handled when the application switches to underscore names? → A: The application only switches to new underscore names; existing dashed collections are not migrated automatically.

## Constitution Constraints *(mandatory)*

- **Hexagonal Architecture**: Business rules belong in `src/core/` and must not import framework/driver
  libraries (e.g., `fastapi`, `pymongo`/`motor`, `ldap3`).
- **Specs-first**: Any change to feature intent, behavioral requirements, or software specifications
  MUST start by updating `specs/`.
- **Canonical contracts**: Any change to shared or canonical data contracts MUST start by updating
  `schemas/`.
- **Inbound validation**: All JSON payload validation occurs in the inbound adapter via Pydantic
  schemas in `src/adapters/inbound/api/schemas/` before calling core use cases.
- **Error mapping**: Domain exceptions live in `src/core/exceptions/` and are mapped to HTTP in
  `src/infrastructure/errors/` (no stack traces returned to clients).
- **Immutable structure**: Do not add/remove/rename folders from the baseline structure.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Use Renamed Collections Transparently (Priority: P1)

As a backend maintainer, I want persistence code to use underscore-based MongoDB collection names so that the database naming convention matches the service's Python-centric backend standards without changing API behavior.

**Why this priority**: The primary value of the feature is to move the persistence layer to the new naming convention while preserving current application behavior.

**Independent Test**: Can be fully tested by exercising the persistence-backed component, application architecture, and micro affinity group flows and verifying reads and writes succeed against the renamed collections with unchanged HTTP and repository behavior.

**Acceptance Scenarios**:

1. **Given** a repository currently reads from or writes to a dashed collection name, **When** the feature is applied, **Then** the repository uses the underscore-based collection name for the same operation.
2. **Given** a client sends a valid request that persists data, **When** the request completes after the rename, **Then** the service stores and retrieves the same document content and returns the same response semantics as before.

---

### User Story 2 - Keep Repository and Test Configuration Consistent (Priority: P2)

As a developer, I want every repository implementation, Mongo-backed persistence test, and direct MongoDB verification path that references MongoDB collections to use the same underscore-based names so that the service and regression tests stay aligned.

**Why this priority**: Partial renames would create false negatives in tests or runtime mismatches between repository implementations and direct MongoDB verification code.

**Independent Test**: Can be fully tested by running repository and persistence suites and confirming that every collection lookup, seeded document, and verification query references the renamed collections consistently.

**Acceptance Scenarios**:

1. **Given** repository implementations, Mongo-backed persistence tests, and direct MongoDB verification code refer to the same collection, when the rename is complete, then all of those references use the identical underscore-based collection name.
2. **Given** a persistence test seeds or verifies documents directly in MongoDB, **When** the test runs after the rename, **Then** it targets the renamed collection and still passes.

---

### User Story 3 - Preserve Persistence Behavior During the Rename (Priority: P3)

As a service owner, I want the collection rename to change only collection identifiers so that document shape and repository-observable persistence behavior remain intact without adding migration or collection-provisioning logic.

**Why this priority**: The rename is purely a naming and alignment change; altering document structure or repository behavior would introduce unintended persistence risk, while collection provisioning remains outside this feature.

**Independent Test**: Can be fully tested by validating that the same stored payloads, query behavior exercised by repositories, and transactional flows succeed after the rename without any schema or document-shape changes.

**Acceptance Scenarios**:

1. **Given** a collection currently stores documents with a defined structure, **When** the collection name is renamed in application code, **Then** the stored document structure used by the service remains unchanged.
2. **Given** a repository depends on existing query keys and transactional flows, **When** it operates against the renamed collection, **Then** its observable persistence behavior remains unchanged.

### Edge Cases

- A collection already using underscore naming, such as `components` or `component_payload_records`, must not be renamed or otherwise altered.
- Existing dashed collections may still be present in MongoDB after deployment, and this feature does not automatically migrate their data into the underscore-based collections.
- A flow that writes to more than one collection, such as the raw and processed micro affinity group persistence path, must rename every affected collection consistently.
- Persistence tests that query MongoDB directly must be updated together with repository code so they do not continue reading from obsolete dashed collection names.
- Any indexes or collection validation rules required on the underscore-based collections are provisioned outside this feature and must not be created, migrated, or recreated differently by application code in this change.
- Any direct MongoDB verification step that still references a dashed collection name must be updated so the application and persistence tests do not split verification across old and new collection names.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST rename every MongoDB collection currently referenced in kebab-case to an equivalent lowercase snake_case name.
- **FR-002**: The system MUST update all repository-layer collection lookups to use the renamed snake_case collection names exactly.
- **FR-003**: The system MUST update all Mongo-backed persistence test code and direct database verification code that references renamed collections so they use the new snake_case names exactly.
- **FR-004**: The system MUST preserve all current document structures within the renamed collections.
- **FR-005**: The system MUST limit this feature to application-side collection-name references and MUST NOT add automatic collection migration, index recreation, or validation-rule recreation logic.
- **FR-006**: The system MUST preserve current read, write, upsert, and transactional behavior when operating against the renamed collections.
- **FR-007**: The system MUST NOT change REST API endpoint paths as part of this feature.
- **FR-008**: The system MUST NOT change Pydantic request or response model fields as part of this feature.
- **FR-009**: The system MUST NOT change core business logic as part of this feature.
- **FR-010**: Collections that already comply with the lowercase underscore naming convention MUST remain unchanged.
- **FR-011**: The feature MUST include automated regression coverage proving that repository and persistence flows continue to operate correctly against the renamed collections.
- **FR-012**: The feature MUST update the current dashed collection names used for application architectures, raw micro affinity groups, and processed micro affinity groups to underscore-based names.
- **FR-013**: The feature MUST switch application code to the underscore-based collection names without automatically migrating existing dashed collections or their stored data.

## Assumptions

- The current collection names that require renaming are the dashed collection identifiers already used by the service, including `application-architectures`, `micro-affinity-groups`, and `micro-affinity-groups-processed`.
- Collections already using underscore-compatible names, such as `components` and `component_payload_records`, are already compliant and therefore out of scope for renaming.
- Existing dashed collections may remain in the database after this feature ships because automatic migration is not part of this change.
- Environments that require indexes or validation rules on the underscore-based collections must provision them outside this feature; the service does not create or migrate them as part of this change.

### Key Entities *(include if feature involves data)*

- **Collection Name Mapping**: A before-and-after mapping from each dashed MongoDB collection name to its required underscore-based replacement.
- **Persistence Collection Reference**: Any repository implementation, Mongo-backed persistence test assertion, or direct database verification step that targets a MongoDB collection by name.
- **Stored Collection Contract**: The unchanged document structure and repository-observable persistence behavior associated with a collection regardless of its renamed identifier.


## Success Criteria *(mandatory)*


### Measurable Outcomes

- **SC-001**: 100% of MongoDB collection names used by the service that currently contain dashes are replaced with lowercase underscore-based names.
- **SC-002**: 100% of repository and persistence regression tests affected by renamed collections pass without requiring API contract changes.
- **SC-003**: 100% of renamed collection references preserve their pre-change document structure and repository-observable persistence behavior after the rename.
- **SC-004**: 0 REST endpoint path changes, Pydantic field changes, or core business logic changes are introduced as part of this feature.
