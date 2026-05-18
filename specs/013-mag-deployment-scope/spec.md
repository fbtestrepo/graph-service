# Feature Specification: MAG Deployment Scope

**Feature Branch**: `013-mag-deployment-scope`  
**Created**: 2026-05-17  
**Status**: Draft  
**Input**: User description: "Implement a new REST endpoint per the below requirements.

- Path: /v1/micro-affinity-groups/{id}/deployment-scope
- Input: A micro affinity group identifier ({id}) passed as part of the url.

additional url parameter - environment

The (id, environment) pair uniquely identifies a document in the micro_affinity_groups_processed MongoDB collection.

- Validation:
  If the (id, environment) passed to the endpoint is not found in the source data, return a 404 Not Found response.

- JSON Output Casing:
  All JSON keys in the response payload must use snake_case.

- Output Structure:
  The full output schema must match the format specified in the example file: specs/samples/micro-affinity-group/deployment-scope.json
  The payload must contain the following key main elements:
  1. dependency_graph: The resolved dependency graph in an edge list format
  2. deployment_sequence: A transformed array specifying the micro-ag deployment order. The sub-element bypassed_edges lists the graph edges that were excluded from the dependency sequence calculation - applies to cases where cyclical dependencies were found.
  3. micro_ag_id - the id of the micro ag for which the output is being generated
  4. environment - identifies the environment for which the output is being generated
  5. graph_has_cycles - true or false, were cycles detected while resolving the graph
  6. effective_date - timestamp in Zulu time, identifies time of generation of the output

- Graph Resolution Rules:
  Relationships are defined as: Node A depends on Node B (represented as A -> B).
  Given an input node ID:
  a) Include the target input node.
  b) Go exactly 1 hop inverse to the dependency arrow (find the immediate nodes that depend on the input node) and add them to the graph.
  c) Resolve downstream dependencies by following the dependency arrows until no further downstream MAGs remain or the supported 30-hop traversal boundary is reached, then add all discovered nodes and edges within that boundary to the graph.

  Example: If the data defines the chain [A -> B -> C -> D -> E] (where A depends on B, B depends on C, etc.):
  If the input ID is \"C\":
  - 1 hop inverse is \"B\" (Rule b)
  - Downstream chain from C is \"D\" and \"E\" (Rule c)
  - The final resolved edge graph must represent: B -> C -> D -> E

- Deployment Sequence Rules:
  The 'deployment_sequence' element is a topological sort of the resolved graph from Step 1, grouped by parallel execution layers:
  - Layer 1: Deploy all nodes that have no remaining dependencies.
  - Layer 2: Deploy the nodes whose dependencies were satisfied in Layer 1, etc.

- Source Data:
  The dependency graph must be derived by querying and joining documents in the 'micro_affinity_groups_processed' MongoDB Atlas collection.
  A sample of these documents can be found in: specs/samples/micro-affinity-group/micro-affinity-group-relationships.json"

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
- **Traversal error semantics**: For graph-traversal or graph-resolution endpoints, `404` MUST be
  used only when the primary resource named in the URL path does not exist; if that resource
  exists but downstream graph resolution fails because dependent records are missing or corrupted,
  the system MUST return `422 Unprocessable Entity`.
- **Immutable structure**: Do not add/remove/rename folders from the baseline structure.

## Clarifications

### Session 2026-05-17

- Q: When a cycle must be broken, which edge should be bypassed? → A: Bypass the lexicographically smallest MAG edge by `(source_micro_ag_id, destination_micro_ag_id)` and repeat until the graph is acyclic.
- Q: Which MAGs belong in deployment Layer 1? → A: Layer 1 contains MAGs with no outgoing dependency edges in the reduced graph, because `A -> B` means `A` depends on `B` and dependencies must deploy first.
- Q: How should items be ordered within deployment steps and edge lists? → A: Sort `micro_ag_ids` lexicographically ascending within each deployment step. Sort `deployment_sequence.bypassed_edges` lexicographically ascending by `(source_micro_ag_id, destination_micro_ag_id)`. In `dependency_graph`, sort non-cyclic edges lexicographically ascending by `(source_micro_ag_id, destination_micro_ag_id)` and append any `is_cyclic = true` bypassed edges after the non-cyclic edges, also lexicographically ascending, to match the sample response contract.

## User Scenarios & Testing *(mandatory)*
### User Story 1 - Retrieve Deployment Scope (Priority: P1)

As an API client, I want to request deployment scope for one micro affinity group in one environment so that I can see the resolved MAG dependency graph and the grouped deployment order needed to roll out that group safely.

**Why this priority**: This is the primary business outcome of the feature: produce a deployment-scope document for a known MAG and environment.

**Independent Test**: Can be fully tested by seeding processed MAG documents for one environment, calling `GET /v1/micro-affinity-groups/{id}/deployment-scope?environment=...`, and verifying the response matches the documented snake_case output structure and graph-resolution rules.

**Acceptance Scenarios**:

1. **Given** a processed MAG document exists for `micro_ag_id = C` in one environment and the related processed documents in that same environment resolve the chain `B -> C -> D -> E`, **When** the client requests deployment scope for `C`, **Then** the service returns `200 OK` with a snake_case response whose dependency graph represents `B -> C -> D -> E` and whose deployment sequence is derived from that resolved graph.
2. **Given** a processed MAG document exists for the requested `micro_ag_id` and environment but has no qualifying one-hop inverse dependents and no downstream dependencies, **When** the client requests deployment scope, **Then** the service still returns `200 OK` with the requested `micro_ag_id`, the requested `environment`, an empty dependency graph, and a deployment sequence that contains the target MAG by itself.

---

### User Story 2 - Classify Missing Root And Broken Graphs Correctly (Priority: P2)

As an API client, I want the endpoint to distinguish a missing requested MAG from a broken downstream graph so that I can tell whether the input identifier is wrong or the source graph data is incomplete.

**Why this priority**: A deployment-scope endpoint is only reliable if it preserves the constitution rule that missing roots are `404` and downstream resolution failures after the root exists are `422`.

**Independent Test**: Can be fully tested by calling the endpoint once with a missing `(micro_ag_id, environment)` pair and once with an existing root whose downstream join cannot be resolved, then verifying `404` for the first case and `422` for the second.

**Acceptance Scenarios**:

1. **Given** no processed MAG document exists for the requested `micro_ag_id` and environment pair, **When** the client requests deployment scope, **Then** the service returns `404 Not Found`.
2. **Given** the requested processed MAG document exists but at least one required downstream relationship cannot be resolved to a unique target MAG in the same environment, **When** the client requests deployment scope, **Then** the service returns `422 Unprocessable Entity` and does not report that the root MAG was missing.

---

### User Story 3 - Surface Cycles In Deployment Planning (Priority: P3)

As an API client, I want cyclic dependencies surfaced explicitly in both the graph and the deployment sequence so that I can understand which edges were bypassed to compute an executable rollout order.

**Why this priority**: Deployment planning loses operational value if cycle handling is hidden or non-deterministic.

**Independent Test**: Can be fully tested by seeding a cyclic MAG graph, requesting deployment scope, and verifying that the response sets `graph_has_cycles` to `true`, flags bypassed cyclic edges, and groups the remaining deployment order into deterministic steps.

**Acceptance Scenarios**:

1. **Given** the resolved MAG graph contains a cycle, **When** the client requests deployment scope, **Then** the service returns `200 OK` with `graph_has_cycles = true`, includes the bypassed cycle-breaking edges in `deployment_sequence.bypassed_edges`, and marks those same edges as cyclic in `dependency_graph`.
2. **Given** multiple MAGs become deployable at the same time after prior layers are satisfied, **When** the deployment sequence is generated, **Then** those MAGs appear together in the same deployment step.
3. **Given** a resolved reduced graph where one MAG depends on another via `A -> B`, **When** the deployment sequence is generated, **Then** `B` appears in an earlier deployment step than `A`.

### Edge Cases

- The requested root MAG exists but has no inverse one-hop dependents and no downstream dependencies; the response must still include the root MAG in the deployment sequence.
- Two or more workload-level relationships resolve to the same MAG-to-MAG dependency edge; the output must not duplicate the same MAG edge.
- A relationship destination matches more than one processed MAG in the same environment; the graph resolution is ambiguous and must fail.
- Matching MAG documents exist in other environments but not in the requested environment; those documents must be ignored completely.
- The resolved graph contains one or more cycles, including self-dependencies.
- A downstream relationship references a workload that is missing, stale, or otherwise unresolvable in the requested environment after the root MAG has already been found.
- The root MAG document is malformed such that required relationship or workload data cannot be interpreted to continue graph resolution.
- A downstream chain extends beyond the supported traversal boundary; the response must include only the first 30 downstream hops and stop cleanly without including hop-31 MAGs.
- Multiple cycle-breaking candidates are present in the same graph; the same edges must be bypassed on repeated requests against unchanged data.
- The reduced graph contains both incoming and outgoing edges for a MAG; deployment eligibility must be based on absence of remaining outgoing dependency edges, not incoming edges.
- Multiple MAGs are eligible in the same deployment step; their ordering must remain stable across repeated requests.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose a read-only REST endpoint at `/v1/micro-affinity-groups/{id}/deployment-scope`.
- **FR-002**: The endpoint MUST require the path parameter `id` and a required query parameter `environment`.
- **FR-003**: The pair of requested `id` and `environment` MUST be used to find the root document in the `micro_affinity_groups_processed` collection.
- **FR-004**: If no root document exists for the requested `id` and `environment`, the system MUST return `404 Not Found`.
- **FR-005**: Successful responses MUST use snake_case for all JSON keys.
- **FR-006**: A successful response body MUST conform to the structure illustrated by `specs/samples/micro-affinity-group/deployment-scope.json`.
- **FR-007**: A successful response body MUST contain the top-level keys `micro_ag_id`, `environment`, `effective_date`, `graph_has_cycles`, `dependency_graph`, and `deployment_sequence`.
- **FR-008**: `micro_ag_id` in the response MUST equal the requested root MAG identifier.
- **FR-009**: `environment` in the response MUST equal the requested environment.
- **FR-010**: `effective_date` in the response MUST be the UTC generation time expressed in Zulu timestamp format.
- **FR-011**: The deployment-scope graph MUST be derived only from documents in `micro_affinity_groups_processed` for the requested environment.
- **FR-012**: The resolved node set MUST always include the requested root MAG even when no edges are discovered.
- **FR-013**: The resolved graph MUST include only the immediate one-hop inverse dependents of the root MAG and MUST NOT recurse further upstream beyond that single hop.
- **FR-014**: The resolved graph MUST recursively include every downstream dependency reachable from the root MAG by following dependency arrows until no further downstream MAGs remain or the supported 30-hop downstream traversal boundary is reached.
- **FR-014a**: The system MUST retain every node and edge discovered within the first 30 downstream hops from the root MAG and MUST stop traversal cleanly without including hop-31 downstream nodes.
- **FR-015**: The service MUST derive MAG-to-MAG dependency edges by joining processed MAG relationship destinations to workload ownership in other processed MAG documents within the same environment.
- **FR-016**: When multiple workload-level joins produce the same source MAG and destination MAG pair, the response MUST contain that MAG edge only once.
- **FR-017**: Each `dependency_graph` entry MUST contain `source_micro_ag_id` and `destination_micro_ag_id`.
- **FR-018**: A `dependency_graph` entry that is bypassed to break a cycle MUST also include `is_cyclic = true`.

- **FR-019**: The system MUST return `422 Unprocessable Entity` when the root MAG exists but any required downstream or intermediate graph join cannot be resolved consistently in the requested environment, including cases where a required downstream join resolves to zero candidates, more than one candidate, or malformed source data prevents consistent resolution.
- **FR-020**: The system MUST NOT return `404 Not Found` for downstream graph-resolution failures after the root MAG has been found.
- **FR-021**: `graph_has_cycles` MUST be `true` when one or more resolved MAG edges are bypassed to compute a valid deployment sequence, and `false` otherwise.
- **FR-022**: `deployment_sequence` MUST contain the keys `bypassed_edges` and `steps`.
- **FR-023**: `deployment_sequence.bypassed_edges` MUST list every MAG edge excluded from the deployment ordering calculation because of cycle handling.
- **FR-024**: `deployment_sequence.steps` MUST be an ordered list of execution layers where each step contains `step_index` and `micro_ag_ids`.
- **FR-025**: The deployment sequence MUST be a topological ordering of the resolved graph after excluding bypassed cycle edges.
- **FR-025a**: When cycle handling is required, the system MUST bypass the lexicographically smallest MAG edge by `(source_micro_ag_id, destination_micro_ag_id)` among the remaining cycle-breaking candidates, then repeat the same rule until the reduced graph is acyclic.
- **FR-026**: For deployment-sequence generation, a MAG is eligible for the current step only when it has no remaining outgoing dependency edges in the reduced graph.
- **FR-026a**: The system MUST interpret a MAG edge `A -> B` as `A` depends on `B`, so `B` must appear in the same or an earlier deployment step than `A`, and never later.
- **FR-027**: If more than one MAG is eligible in the same layer, the system MUST place them in the same step.
- **FR-028**: If the resolved graph contains no edges, the deployment sequence MUST still contain one step with the root MAG identifier.
- **FR-029**: The service MUST order `micro_ag_ids` within each deployment step lexicographically ascending by `micro_ag_id`.
- **FR-030**: The service MUST order `deployment_sequence.bypassed_edges` lexicographically ascending by `(source_micro_ag_id, destination_micro_ag_id)`. The service MUST order `dependency_graph` deterministically by listing non-cyclic edges first in lexicographic ascending order by `(source_micro_ag_id, destination_micro_ag_id)`, followed by any `is_cyclic = true` bypassed edges in lexicographic ascending order, so repeated calls against unchanged source data produce the same output ordering and remain aligned with `specs/samples/micro-affinity-group/deployment-scope.json`.
- **FR-031**: The endpoint MUST NOT persist new deployment-scope documents as part of this feature.
- **FR-032**: The feature MUST include automated regression coverage for successful graph resolution, empty-graph resolution, cycle handling, missing-root `404`, and downstream-resolution `422` behavior.

## Assumptions

- `environment` is provided as a required query parameter rather than as an additional path segment or request header.
- Processed MAG documents are the authoritative source for this endpoint; raw MAG documents are not queried for graph resolution.
- A workload in one environment belongs to at most one processed MAG for successful graph resolution. If that assumption is violated in stored data, the request is treated as an ambiguous downstream-resolution failure.
- Only documents from the requested environment participate in graph resolution, even if identical workloads or MAG identifiers exist in other environments.
- The response sample file is the authoritative service-level output contract for this feature.
- When multiple edges could be bypassed to break cycles, deterministic lexicographic selection is part of the public contract for stable outputs.
- Deployment-layer eligibility is determined from outgoing dependency edges in the reduced MAG graph rather than incoming edges.
- Stable ordering of step contents and edge lists is part of the public response contract: `micro_ag_ids` and `deployment_sequence.bypassed_edges` are lexicographically ordered, while `dependency_graph` keeps non-cyclic edges before cyclic bypassed edges to match the sample contract.

### Key Entities *(include if feature involves data)*

- **Deployment Scope Response**: The generated response document containing the requested root MAG identity, environment, generation timestamp, resolved dependency graph, cycle indicator, and grouped deployment sequence.
- **MAG Dependency Edge**: A directed MAG-to-MAG edge represented by `source_micro_ag_id` and `destination_micro_ag_id`, where the source MAG depends on the destination MAG.
- **Deployment Step**: One execution layer in the deployment sequence containing a `step_index` and the set of MAG identifiers that can be deployed in parallel.
- **Bypassed Edge**: A resolved MAG dependency edge that is excluded from the deployment ordering calculation to break a cycle but is still surfaced in the response.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In seeded acceptance testing that mirrors the sample contract, 100% of requests for a resolvable root MAG return a response matching the documented deployment-scope structure and the expected MAG dependency edges.
- **SC-002**: In acceptance testing, 100% of requests for a missing `(micro_ag_id, environment)` pair return `404 Not Found`, and 100% of requests for an existing root with a broken downstream graph return `422 Unprocessable Entity`.
- **SC-003**: In regression testing, 100% of successful responses use snake_case keys for all documented fields.
- **SC-004**: In regression testing for cyclic graphs, 100% of successful responses set `graph_has_cycles` correctly and include bypassed edges plus layered deployment steps consistent with the reduced graph.
- **SC-005**: In regression testing for the same unchanged cyclic source graph, repeated requests return the same `bypassed_edges` set and the same deployment-step ordering in 100% of attempts.
- **SC-006**: In regression testing for every resolved edge `A -> B`, 100% of successful responses place `B` in an earlier or equal deployment layer relative to `A`, never in a later one.
- **SC-007**: In regression testing, 100% of repeated successful responses against unchanged source data return lexicographically ordered `micro_ag_ids` within each step, lexicographically ordered `deployment_sequence.bypassed_edges`, and deterministically ordered `dependency_graph` entries with non-cyclic edges before cyclic bypassed edges.
- **SC-008**: In regression testing with a downstream chain longer than 30 hops, 100% of successful responses include all nodes and edges through hop 30 and exclude hop-31 downstream nodes.
