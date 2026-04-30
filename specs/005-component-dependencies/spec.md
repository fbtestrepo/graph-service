# Feature Specification: Component Dependencies Graph

**Feature Branch**: `005-component-dependencies`  
**Created**: 2026-03-26  
**Status**: Draft  
**Input**: User description: "Implement a new endpoint /components/{node_id}/dependencies per the below requirements: Input: A node_id representing the root component. Output: A full transitive dependency graph (upstream and downstream) in the 'edge list' format defined in specs/sample-component-dependencies/sample-mag-dependencies.json. Behavior: The graph must include all direct and indirect relationships. Validation: If the node-id does not exist, return a 404 Not Found. Source Data: Relationships are defined by the schema found in specs/sample-component-payload/sample-mag.json. This is the schema of the documents passed to the components endpoint and persisted in MongoDB Atlas"

## Constitution Constraints *(mandatory)*

- **Hexagonal Architecture**: Business rules belong in `src/core/` and must not import framework/driver
  libraries (e.g., `fastapi`, `pymongo`/`motor`, `ldap3`).
- **Specs-first**: Any API contract change MUST start by updating `specs/` (OpenAPI + JSON Schemas).
- **Inbound validation**: All JSON payload validation occurs in the inbound adapter via Pydantic
  schemas in `src/adapters/inbound/api/schemas/` before calling core use cases.
- **Error mapping**: Domain exceptions live in `src/core/exceptions/` and are mapped to HTTP in
  `src/infrastructure/errors/` (no stack traces returned to clients).
- **Immutable structure**: Do not add/remove/rename folders from the baseline structure.

## Clarifications

### Session 2026-03-26

- Q: How should the 20-hop traversal limit apply at the boundary (depth 20)? → A: Include boundary cycle edges: expand/query edges for depth-20 nodes only to include edges whose other endpoint is already in-scope (depth ≤ 20), but do not include edges that would introduce any new node beyond depth 20, and do not enqueue further expansion.
- Q: When extracting dependency edges from stored component-node documents, how should we treat a relationship where `relationships[i].source.node-id` does not equal the document’s top-level `node-id`? → A: Filter to “self-sourced” only: only emit relationships where `relationship.source.node-id == document.node-id`; ignore the rest.
- Q: How should we define reachability + hop count when we say “upstream and downstream” with a 20-hop cap? → A: Two directed traversals from the root: compute (1) downstream closure by following `source-node-id → target-node-id` only, and (2) upstream closure by following `target-node-id → source-node-id` only. Union the results. Apply the 20-hop cap within each directed traversal (relative to the root).

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Retrieve Dependencies (Priority: P1)

**As a** client of the service, **I want** to retrieve the complete transitive dependency graph for a component node, **so that** I can understand all direct and indirect dependencies upstream and downstream of that component.

**Why this priority**: This endpoint enables the primary business value: exploring the dependency neighborhood of a component from existing stored relationship data.

**Independent Test**: Can be fully tested by storing a small chain/graph of component nodes (with relationships) and calling `GET /components/{node_id}/dependencies` to verify the returned edge list includes all direct and indirect relationships.

**Acceptance Scenarios**:

1. **Given** a root component node exists and has at least one direct relationship to another node, **When** the client requests its dependencies, **Then** the service returns `200 OK` with an edge list containing at least that direct relationship.
2. **Given** a root component node exists and there are indirect relationships reachable through other nodes, **When** the client requests its dependencies, **Then** the service returns `200 OK` with an edge list containing both direct and indirect relationships.
3. **Given** a root component node exists but has no relationships and no other nodes reference it, **When** the client requests its dependencies, **Then** the service returns `200 OK` with an empty edge list.
4. **Given** the reachable dependency subgraph contains cycles, **When** the client requests its dependencies, **Then** the service returns `200 OK` and includes each discovered edge at most once.

---

### User Story 2 - Missing Root Node Returns Not Found (Priority: P2)

**As a** client of the service, **I want** a clear not-found response when the root `node-id` does not exist, **so that** I can distinguish “unknown component” from “known component with no dependencies”.

**Why this priority**: Without a `404`, clients cannot safely tell whether they used the wrong `node-id`.

**Independent Test**: Can be tested by calling the endpoint with a `node-id` that is not present in stored component nodes and verifying the response is `404 Not Found`.

**Acceptance Scenarios**:

1. **Given** no stored component node exists with `node-id = X`, **When** the client requests dependencies for `X`, **Then** the service returns `404 Not Found`.

---

### User Story 3 - Stable, Deduplicated Edge Lists (Priority: P3)

**As a** client of the service, **I want** a dependency edge list that is stable and free of duplicate edges, **so that** I can compare results over time and avoid client-side de-duplication.

**Why this priority**: Stable output reduces client complexity and makes the endpoint easier to use in automation.

**Independent Test**: Can be tested by creating multiple stored relationship records that could lead to duplicates and verifying the output contains each unique edge exactly once in a stable order.

**Acceptance Scenarios**:

1. **Given** the reachable subgraph contains the same relationship edge multiple times (from repeated submissions or repeated discovery paths), **When** the client requests dependencies, **Then** the service returns a response containing each unique edge only once.

---

### Edge Cases

- Root node exists but has no `relationships` field.
- Graph contains cycles (e.g., A → B → A).
- Graph contains self-referential edges (A → A).
- Multiple edges exist between the same pair of nodes (different `relationship-type` values).
- Some edges reference node-ids that do not exist as stored component nodes.
- Large reachable subgraph (many nodes/edges) still returns a complete, deduplicated result.
- Traversal depth boundary at 20 hops.
- Relationship record where `relationship.source.node-id != document.node-id`.
- Reachability/hop definition for “upstream” vs “downstream”.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose an HTTP endpoint to retrieve dependencies for a component identified by `node-id`.
- **FR-002**: The endpoint MUST accept a node_id as a path parameter (value is the component node-id) and treat it as the root component identifier.
- **FR-003**: If the root `node-id` does not exist in stored component nodes, the system MUST return `404 Not Found`.
- **FR-004**: If the root `node-id` exists, the system MUST return `200 OK` with a response body in the edge list format shown in `specs/sample-component-dependencies/sample-mag-dependencies.json`.
- **FR-005**: The response body MUST be a JSON object containing:
  - `node-id`: the requested root `node-id`
  - `dependency-graph`: an array of dependency edges
- **FR-006**: Each dependency edge MUST be a JSON object containing:
  - `relationship-type` (string)
  - `source-node-id` (string)
  - `target-node-id` (string)
- **FR-007**: Dependency edges MUST be derived from stored component-node relationship data (as provided to the existing components upsert endpoint). Each stored relationship contributes an edge from the relationship’s `source.node-id` to `target.node-id` with the same `relationship-type`.
- **FR-008**: The returned dependency graph MUST be transitive and MUST include all direct and indirect relationships reachable from the root when considering both:
  - downstream reachability (following edges from `source-node-id` → `target-node-id`)
  - upstream reachability (following edges in reverse direction)
- **FR-009**: The system MUST avoid infinite loops when cycles exist and MUST include each unique edge at most once.
- **FR-010**: The system MUST return a stable, deterministic ordering of edges for the same underlying stored data. Edges MUST be ordered by `relationship-type`, then `source-node-id`, then `target-node-id` (all ascending lexical order).
- **FR-011**: If an edge references a node-id that does not exist as a stored component node, the system MUST still include that edge in the returned edge list; indirect expansion beyond missing nodes is not required.
- **FR-012**: The system MUST NOT require clients to specify whether they want upstream vs downstream; the response MUST include both.
- **FR-013**: The system MUST cap traversal at 20 hops from the root. At the boundary (depth 20), the system MAY fetch/include edges incident to depth-20 nodes only when both endpoints are already within ≤ 20 hops from the root; the system MUST NOT include edges that would introduce a node beyond 20 hops, and MUST NOT expand beyond depth 20.
- **FR-014**: When extracting edges from a stored component node document, the system MUST only include relationship records where `relationship.source.node-id == document.node-id`.
- **FR-015**: To satisfy “upstream and downstream” reachability, the system MUST compute:
  - downstream reachability by traversing edges in the forward direction (`source-node-id → target-node-id`) starting from the root, and
  - upstream reachability by traversing edges in the reverse direction (`target-node-id → source-node-id`) starting from the root,

  then return the union of edges discovered by both traversals. The 20-hop cap (and boundary behavior in FR-013) MUST apply separately within each directed traversal relative to the root.

Assumptions (non-functional scope notes):

- The dependencies endpoint is exposed under the existing `/components` resource namespace (i.e., `GET /components/{node_id}/dependencies`).
- All stored relationship types are treated as dependency edges for the purpose of graph traversal.
- Authorization/authentication behavior is unchanged from existing endpoints.

### Key Entities *(include if feature involves data)*

- **Component Node**: A stored component record uniquely identified by `node-id`, containing optional relationship definitions to other nodes.
- **Dependency Edge**: A directed relationship between two component nodes represented by (`relationship-type`, `source-node-id`, `target-node-id`).
- **Dependency Graph**: A set of dependency edges representing all relationships reachable upstream and downstream from a root component node.

## Success Criteria *(mandatory)*


### Measurable Outcomes

- **SC-001**: For a known dataset that matches the example in `specs/sample-component-dependencies/sample-mag-dependencies.json`, requesting dependencies for the example root returns an edge list that matches the expected edges exactly.
- **SC-002**: When requesting dependencies for a `node-id` that does not exist, the system returns `404 Not Found` in 100% of attempts.
- **SC-003**: For a reachable dependency subgraph containing at least 100 unique edges, at least 95 out of 100 sequential requests (after a warm-up of 5 requests, not counted) complete within 1.0 seconds as observed by the client.
- **SC-004**: For a reachable dependency subgraph that contains at least one cycle, the endpoint returns successfully and the result contains no duplicate edges.
