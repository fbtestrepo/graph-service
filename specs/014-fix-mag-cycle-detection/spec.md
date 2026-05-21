# Feature Specification: Fix MAG Cycle Detection

**Feature Branch**: `014-fix-mag-cycle-detection`  
**Created**: 2026-05-18  
**Status**: Draft  
**Input**: User description: "An issue has been identified when the deployment-scope graph being resolved contains cycles. For the graph `A -> C`, `B -> C`, `C -> D`, `D -> E`, `F -> E`, `G -> F`, `E -> E1`, `E -> E2`, `E -> E3`, `E1 -> C`, the deployment-scope response for root `C` currently marks `C -> D` as cyclic and returns incorrect deployment stages. The correct behavior is to treat `E1 -> C` as the cyclic back-edge because it points back to a node already on the current root-scoped traversal path after the required one-hop-upstream boundary has been established, then exclude that back-edge from deployment-step calculation while preserving the remaining graph." 

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

## Assumptions

- The affected endpoint remains `GET /v1/micro-affinity-groups/{id}/deployment-scope` with the same request and response schema already defined for Feature 013.
- No feature changes are required for acyclic graphs; the defect scope is limited to cycle identification and deployment sequencing when cycles are present.
- The existing one-hop-upstream boundary rule still applies before any downstream traversal begins.
- A path-scoped cyclic edge is any resolved MAG edge whose destination MAG already appears earlier on the same root-scoped traversal path.
- When one or more path-scoped cyclic edges are identified, those edges remain visible in `dependency_graph`, are flagged with `is_cyclic = true`, are listed in `deployment_sequence.bypassed_edges`, and are excluded from deployment-step calculation.

## User Scenarios & Testing *(mandatory)*
### User Story 1 - Mark The Correct Back-Edge (Priority: P1)

As an API client, I want the deployment-scope response to mark the true cycle-closing back-edge in a cyclic graph so that the response reflects the actual root-scoped traversal path instead of bypassing a non-cyclic downstream edge.

**Why this priority**: Incorrect cycle marking produces a materially wrong dependency graph and leads directly to incorrect deployment planning for cyclic graphs.

**Independent Test**: Can be fully tested by seeding the graph `A -> C`, `B -> C`, `C -> D`, `D -> E`, `E -> E1`, `E1 -> C`, `E -> E2`, `E -> E3`, `F -> E`, `G -> F`, requesting deployment scope for `C`, and verifying that `E1 -> C` is the only edge flagged as cyclic, `C -> D` remains a normal dependency edge, and the immediate upstream consumer edges `A -> C` and `B -> C` remain included and non-cyclic.

**Acceptance Scenarios**:

1. **Given** a resolved root-scoped path for `C` reaches `C -> D -> E -> E1` and the edge `E1 -> C` points back to `C` already on that same path, **When** the client requests deployment scope for `C`, **Then** the response marks `E1 -> C` with `is_cyclic = true`, includes it in `deployment_sequence.bypassed_edges`, and does not mark `C -> D` as cyclic.
2. **Given** the resolved graph for `C` includes immediate one-hop upstream consumers `A` and `B`, **When** cycle handling is applied, **Then** those upstream edges remain non-cyclic and are not candidates for bypass unless they themselves close a path-scoped cycle.

---

### User Story 2 - Produce Correct Deployment Stages After Cycle Removal (Priority: P2)

As an API client, I want deployment stages to be calculated from the resolved graph after excluding only the true back-edge so that the rollout sequence matches the dependency structure that remains after cycle handling.

**Why this priority**: Even if the graph exposes the right cyclic edge, the feature is still operationally wrong if the deployment steps are built from the wrong reduced graph.

**Independent Test**: Can be fully tested using the same cyclic dataset by verifying that the reduced graph produces the five deployment steps `E1/E2/E3`, then `E`, then `D`, then `C`, then `A/B`.

**Acceptance Scenarios**:

1. **Given** the graph for root `C` contains the path-scoped back-edge `E1 -> C`, **When** deployment steps are generated, **Then** the system excludes only `E1 -> C` from the deployment-step calculation and returns five ordered steps with `E1`, `E2`, and `E3` together first, followed by `E`, then `D`, then `C`, then `A` and `B` together.
2. **Given** more than one MAG is eligible at the same stage after the cyclic back-edge has been removed, **When** deployment steps are returned, **Then** those MAGs appear together in the same step and stay deterministically ordered.

---

### User Story 3 - Preserve Correct Behavior For Acyclic Graphs (Priority: P3)

As an API client, I want non-cyclic deployment-scope responses to remain unchanged so that fixing cyclic traversal does not regress the behavior of already-correct acyclic graph resolution.

**Why this priority**: The issue is explicitly scoped to cyclic graphs, so the fix must not change behavior where no defect exists.

**Independent Test**: Can be fully tested by re-running the existing acyclic deployment-scope scenarios in `tests/test_micro_affinity_group_deployment_scope_use_case.py`, `tests/test_micro_affinity_group_deployment_scope_endpoint.py`, and `tests/test_micro_affinity_group_deployment_scope_persistence.py` and verifying that dependency graphs, step grouping, and non-cycle flags remain unchanged.

**Acceptance Scenarios**:

1. **Given** the existing acyclic deployment-scope scenarios already covered in `tests/test_micro_affinity_group_deployment_scope_use_case.py`, `tests/test_micro_affinity_group_deployment_scope_endpoint.py`, and `tests/test_micro_affinity_group_deployment_scope_persistence.py`, **When** the client requests deployment scope after this fix, **Then** the response remains unchanged from the currently asserted expected behavior, with `graph_has_cycles = false`, no bypassed edges, and the same deployment stages as before the fix.

### Edge Cases

- A root-scoped traversal reaches a node by more than one non-cyclic path before any back-edge is encountered; only edges that point back to a node already on the current active path are cyclic.
- The resolved graph contains upstream consumers outside the cycle and downstream branches outside the cycle; those non-cyclic branches must remain in `dependency_graph` and continue to influence deployment stages normally.
- Removing the true path-scoped back-edge causes multiple MAGs to become deployable in the same stage; those MAGs must be grouped together, not split across sequential stages.
- A cyclic graph contains no ambiguity about the back-edge on the active path, but multiple non-cyclic outgoing edges exist from the same node; non-cyclic edges must not be bypassed merely because they appear earlier in a global sort order.
- Graphs with no cycles must continue to return their existing correct behavior unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preserve the existing request contract and top-level response contract for `GET /v1/micro-affinity-groups/{id}/deployment-scope`.
- **FR-002**: For cyclic graphs, the system MUST identify a cyclic edge only when that edge points to a MAG already present earlier on the current root-scoped traversal path.
- **FR-003**: The system MUST establish the root-scoped traversal boundary by first including the requested root MAG and exactly one hop of immediate upstream consumers before resolving downstream dependencies.
- **FR-004**: The system MUST NOT classify a downstream edge as cyclic unless its destination MAG already appears on the current active traversal path.
- **FR-005**: In the reported graph rooted at `C`, the system MUST treat `E1 -> C` as the cyclic edge and MUST NOT treat `C -> D` as cyclic.
- **FR-006**: Any edge identified as cyclic by the path-scoped rule MUST remain present in `dependency_graph`, MUST include `is_cyclic = true`, and MUST also appear in `deployment_sequence.bypassed_edges`.
- **FR-007**: Deployment steps MUST be calculated from the resolved graph after excluding only the edges listed in `deployment_sequence.bypassed_edges`.
- **FR-008**: For the reported graph rooted at `C`, the deployment steps MUST be returned as five stages: `E1/E2/E3`, then `E`, then `D`, then `C`, then `A/B`.
- **FR-009**: MAGs that become deployable simultaneously after removing path-scoped cyclic edges MUST be grouped into the same deployment step.
- **FR-010**: Non-cyclic graphs MUST preserve their current correct dependency-graph output, `graph_has_cycles` value, bypassed-edge list, and deployment-step calculation.
- **FR-011**: The fix MUST apply without changing the existing `404` versus `422` semantics for deployment-scope resolution, and this MUST be confirmed by re-running the existing deployment-scope error-classification regressions.
- **FR-012**: The feature MUST include automated regression coverage for the reported cyclic graph, including both the corrected cyclic-edge selection and the corrected deployment stages.

### Key Entities *(include if feature involves data)*

- **Root-Scoped Traversal Path**: The ordered sequence of MAGs visited while resolving deployment scope after establishing the one-hop-upstream boundary for a requested root MAG.
- **Path-Scoped Cyclic Edge**: A resolved MAG edge whose destination MAG already appears earlier on the current root-scoped traversal path.
- **Reduced Deployment Graph**: The resolved dependency graph after excluding all path-scoped cyclic edges from deployment-stage calculation.
- **Deployment Stage**: A single ordered execution step containing all MAGs whose remaining downstream dependencies in the reduced deployment graph have already been satisfied.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In regression testing for the reported cyclic graph rooted at `C`, 100% of successful responses mark `E1 -> C` as the only cyclic edge and do not mark `C -> D` as cyclic.
- **SC-002**: In regression testing for the reported cyclic graph rooted at `C`, 100% of successful responses return exactly five deployment stages with the expected MAG membership in each stage.
- **SC-003**: In regression testing for the existing acyclic deployment-scope scenarios covered by `tests/test_micro_affinity_group_deployment_scope_use_case.py`, `tests/test_micro_affinity_group_deployment_scope_endpoint.py`, and `tests/test_micro_affinity_group_deployment_scope_persistence.py`, 100% of successful responses remain identical to the currently asserted dependency-graph and deployment-stage outputs.
- **SC-004**: In regression testing for cyclic graphs, 100% of bypassed edges correspond to edges whose destination MAG already appeared earlier on the same active traversal path used to detect the cycle.
- **SC-005**: In regression testing for at least one additional cyclic graph shape beyond the reported example, 100% of successful responses mark as cyclic only edges whose destination MAG already appears on the current active traversal path.
