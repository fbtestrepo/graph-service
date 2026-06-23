# Feature Specification: Deploy-Scope Graph Resolution Fix

**Feature Branch**: `015-fix-deploy-scope-graph`  
**Created**: 2026-06-20  
**Status**: Draft  
**Input**: User description: "Fix deploy-scope graph resolution so one-hop upstream dependents are included first, then traversed downstream; detect cyclic edges only when an edge points to a node already on the current traversal path; move those cyclic edges to bypassed edges and exclude them from deployment-step topological ordering."

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

### Session 2026-06-20

- Q: Which endpoint contract should this feature target? → A: Keep existing endpoint contract unchanged: `/v1/micro-affinity-groups/{id}/deployment-scope`.
- Q: Which error semantic should this feature preserve for graph-resolution failures? → A: Preserve current rule: `404` only when requested root MAG is missing; `422` when root exists but downstream graph resolution fails.
- Q: How should response ordering be defined? → A: Make ordering contractual and deterministic: sort `micro_ag_ids` lexicographically within each deployment step and keep steps ordered by `step_index`.
- Q: How should traversal-path visited initialization be defined before downstream DFS? → A: Initialize each traversal branch visited list with the root plus all immediate one-hop upstream dependents before downstream DFS begins.
- Q: How should dependency_graph edge ordering handle cyclic edges? → A: Use deterministic hybrid ordering: list non-cyclic edges first (lexicographic by `(source_micro_ag_id, destination_micro_ag_id)`), then cyclic edges (also lexicographic).

## User Scenarios & Testing *(mandatory)*
### User Story 1 - Resolve Full Scope From One-Hop Upstream Seeds (Priority: P1)

As an API consumer, I want the deploy-scope graph to include downstream dependencies that originate from the immediate one-hop upstream dependents of the requested micro affinity group, so the returned scope is complete for deployment planning.

**Why this priority**: This fixes the primary defect where valid graph edges are currently missing from the output.

**Independent Test**: Can be fully tested by loading the provided dependency set and requesting deploy scope for `C`; the returned edge list must include both one-hop upstream edges into `C` and downstream edges discovered through those upstream seeds.

**Acceptance Scenarios**:

1. **Given** dependencies `A -> C`, `B -> C`, `C -> D`, `D -> E`, `E -> E1`, `E -> E2`, `E -> E3`, `E1 -> C`, **When** deploy scope is requested for `C`, **Then** the graph includes `A -> C`, `B -> C`, `C -> D`, `D -> E`, and `E` downstream edges to `E1`, `E2`, and `E3`.
2. **Given** the same dependency set, **When** deploy scope is requested for `E3`, **Then** the graph includes one-hop upstream edge `E -> E3` and downstream traversal from immediate upstream seed `E` through `E1 -> C -> D -> E`.

---

### User Story 2 - Mark Only Path Back-Edges As Cyclic (Priority: P2)

As an API consumer, I want cyclic edges identified only when an edge points to a node already on the current traversal path, so non-cyclic edges are not incorrectly bypassed.

**Why this priority**: Incorrect cycle tagging directly corrupts both graph interpretation and deployment sequencing.

**Independent Test**: Can be fully tested by verifying that cycle flags for roots `C` and `E3` match the expected cyclic edge definitions in the provided examples.

**Acceptance Scenarios**:

1. **Given** root `C` and branch-path initialization that includes `C` plus immediate one-hop upstream dependents `A`, `B`, and `E1`, **When** traversal reaches `... -> D -> E` and evaluates edge `E -> E1`, **Then** that edge is marked cyclic because `E1` is already on the active path.
2. **Given** root `E3` and traversal path that reaches `... -> C -> D`, **When** edge `D -> E` is evaluated, **Then** that edge is marked cyclic because `E` is already on the active path.
3. **Given** an edge whose destination is not already on the active path, **When** it is evaluated, **Then** it is not marked cyclic.

---

### User Story 3 - Keep Deployment Steps Valid After Cycle Bypass (Priority: P3)

As an API consumer, I want deployment steps to be derived from the resolved graph excluding only detected cyclic back-edges, so deployment ordering remains executable and stable.

**Why this priority**: The endpoint must still produce operationally useful rollout steps while surfacing cycle information.

**Independent Test**: Can be fully tested by validating that `bypassed_edges` contains exactly the marked cyclic edges and that step outputs for roots `C` and `E3` match expected layered deployment groups.

**Acceptance Scenarios**:

1. **Given** root `C` and cyclic edge `E -> E1` identified as bypassed for deployment ordering, **When** steps are produced, **Then** step groups match the expected order: `E2/E3`, then `E`, then `D`, then `C`, then `E1/A/B`.
2. **Given** root `E3` and cyclic edge `D -> E` identified as bypassed for deployment ordering, **When** steps are produced, **Then** step groups match the expected order: `D`, then `C`, then `E1/E2/E3`, then `E`.

### Edge Cases

- The requested micro affinity group exists but has no immediate upstream dependents; downstream traversal still starts from the requested node.
- The requested micro affinity group exists and has immediate upstream dependents that have no additional downstream edges; those upstream edges still remain in the graph.
- Multiple traversal branches converge on a shared node; cycle detection must use the current active path, not a global visited set alone.
- A self-loop edge exists (`X -> X`); it is cyclic and must be bypassed for deployment step calculation.
- Multiple cyclic back-edges are encountered in one resolution; every such edge must be marked and bypassed while preserving non-cyclic edges.
- Graph output must remain deterministic when multiple micro affinity groups can be deployed in the same step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preserve the existing deploy-scope endpoint contract at `/v1/micro-affinity-groups/{id}/deployment-scope` and preserve the response shape, including `dependency_graph`, `deployment_sequence`, `micro_ag_id`, `environment`, `graph_has_cycles`, and `effective_date`.
- **FR-002**: For a requested input node, graph resolution MUST first discover exactly one hop upstream dependents (nodes that directly depend on the input node).
- **FR-003**: The system MUST start downstream graph traversal from the immediate one-hop upstream dependents discovered in FR-002.
- **FR-003a**: If no immediate one-hop upstream dependent exists for the input node, the system MUST start downstream traversal from the input node.
- **FR-004**: Downstream traversal MUST continue until no further dependencies are discoverable for the active branch or the fixed 30-hop downstream traversal boundary is reached, whichever occurs first.
- **FR-004a**: The system MUST include nodes and edges discovered through hop 30 and MUST exclude nodes and edges discovered at hop 31 or greater.
- **FR-005**: The resolved dependency graph MUST include all edges reachable by the traversal defined in FR-002 through FR-004.
- **FR-006**: The system MUST maintain a path-sequenced visited list for the current traversal branch.
- **FR-007**: An edge MUST be classified as cyclic only when its destination node already exists in the current branch path-sequenced visited list.
- **FR-008**: Any cyclic edge detected by FR-007 MUST be marked as `is_cyclic: true` in `dependency_graph`.
- **FR-009**: Any cyclic edge detected by FR-007 MUST be added to `deployment_sequence.bypassed_edges` and excluded from deployment-step ordering calculations.
- **FR-010**: Non-cyclic edges MUST remain included in `dependency_graph` and MUST continue to participate in deployment-step ordering calculations.
- **FR-011**: `graph_has_cycles` MUST be `true` if at least one edge is marked cyclic; otherwise it MUST be `false`.
- **FR-012**: For the provided sample graph and input node `C`, the response MUST include `E -> E1` as cyclic and MUST include the non-cyclic edges shown in the expected sample output.
- **FR-013**: For the provided sample graph and input node `E3`, the response MUST include `D -> E` as cyclic and MUST include the non-cyclic edges shown in the expected sample output.
- **FR-014**: Deployment steps MUST remain a valid topological layering over the reduced graph formed by removing bypassed cyclic edges.
- **FR-015**: The feature MUST include automated regression coverage for the sample `C` and `E3` cases, including both edge classification and deployment step outputs.
- **FR-016**: Existing topological-step grouping behavior for acyclic graphs MUST remain unchanged.
- **FR-017**: The feature MUST preserve existing traversal error semantics: return `404 Not Found` only when the requested root MAG does not exist, and return `422 Unprocessable Entity` when the root MAG exists but downstream graph resolution fails.
- **FR-018**: Response ordering MUST be deterministic and contractual: `deployment_sequence.steps` are ordered by `step_index` ascending, and `micro_ag_ids` inside each step are sorted lexicographically ascending.
- **FR-019**: Before downstream traversal begins, the path-sequenced visited list for each branch MUST be initialized with the requested root MAG and all immediate one-hop upstream dependents discovered for that request.
- **FR-020**: `dependency_graph` ordering MUST be deterministic with cyclic-awareness: list non-cyclic edges first sorted lexicographically by `(source_micro_ag_id, destination_micro_ag_id)`, then list cyclic edges sorted lexicographically by `(source_micro_ag_id, destination_micro_ag_id)`.

## Assumptions

- The endpoint path and naming remain unchanged from the current implementation; this feature changes traversal and cycle classification behavior only.
- Existing environment/effective-date sourcing behavior remains unchanged.
- Existing traversal depth and data-validation protections remain in effect; this feature does not change those limits.
- Deterministic ordering behavior for graph edges and deployment steps remains aligned with the current service contract and tests.

## Dependencies

- Dependency relationship records are available and queryable for all nodes involved in graph resolution.
- The service continues to have access to the same environment-scoped source data used by the current deploy-scope endpoint.

### Key Entities *(include if feature involves data)*

- **Input Micro AG**: The requested micro affinity group identifier for which deploy scope is resolved.
- **Dependency Edge**: A directional relationship `source_micro_ag_id -> destination_micro_ag_id` where source depends on destination.
- **Traversal Path**: The ordered branch-local sequence of nodes currently being explored during downstream traversal.
- **Cyclic Edge**: An edge whose destination is already present in the current traversal path.
- **Bypassed Edge**: A cyclic edge excluded from deployment step calculation but still returned in graph outputs.
- **Deployment Step**: A layer containing one or more micro affinity group IDs that can be deployed in parallel based on remaining non-bypassed dependencies.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In automated regression tests for the provided `C` dataset, 100% of expected edges are present and exactly one edge (`E -> E1`) is marked as cyclic.
- **SC-002**: In automated regression tests for the provided `E3` dataset, 100% of expected edges are present and exactly one edge (`D -> E`) is marked as cyclic.
- **SC-003**: In automated regression tests for both `C` and `E3` datasets, 100% of cyclic edges are present in `deployment_sequence.bypassed_edges` and excluded from deployment step ordering.
- **SC-004**: In automated regression tests for both datasets, deployment steps match the expected sample step memberships with 100% consistency across repeated runs on unchanged data.
- **SC-005**: In regression tests for existing acyclic deploy-scope scenarios, 100% of previously passing tests continue to pass with no behavior changes.
