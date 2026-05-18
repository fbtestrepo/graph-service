# Data Model: MAG Deployment Scope

**Branch**: 013-mag-deployment-scope  
**Date**: 2026-05-17

## Overview

This feature introduces a read-only deployment-scope projection for a single processed Micro-AG in
one environment. The projection is computed at request time from
`micro_affinity_groups_processed`, resolves MAG-to-MAG dependency edges from workload-level
relationships, detects cycles, and derives a dependency-first deployment sequence without
persisting any new records.

## Entity: ProcessedMicroAffinityGroupSource

Represents one stored source document in `micro_affinity_groups_processed`.

### Fields Used

- **`micro_ag_id`** (string, required): Logical identifier of the processed MAG.
- **`environment`** (string, required): Environment scope for graph resolution.
- **`effective_date`** (string, required): Existing source timestamp; not reused as response
  generation time.
- **`workloads`** (array, required): Asset ownership list used to determine which MAG owns a
  destination workload.
- **`relationships`** (array, required): Outgoing workload-to-workload relationships already
  resolved during MAG processing.

### Validation / Resolution Rules

- Root lookup uses `micro_ag_id + environment` only.
- Only source documents from the requested environment participate in graph resolution.
- Source documents whose structure is missing fields required for graph resolution are treated as
  downstream-resolution failures once the root exists.

## Entity: MicroAgDependencyEdge

Represents one resolved MAG-to-MAG dependency.

### Fields

- **`source_micro_ag_id`** (string, required): MAG that depends on another MAG.
- **`destination_micro_ag_id`** (string, required): MAG that must deploy before the source MAG.
- **`is_cyclic`** (boolean, optional): Present and `true` only when the edge is selected as a
  bypassed cycle-breaking edge.

### Validation Rules

- Edge uniqueness is based on the pair `(source_micro_ag_id, destination_micro_ag_id)`.
- Self-referential MAG edges are suppressed from normal edge emission.
- Output ordering is lexicographic ascending by `(source_micro_ag_id, destination_micro_ag_id)`.

## Entity: DeploymentStep

Represents one parallel execution layer in the reduced DAG.

### Fields

- **`step_index`** (integer, required, minimum 1): One-based execution order.
- **`micro_ag_ids`** (array of string, required): MAGs that can deploy in parallel at this layer.

### Validation Rules

- `micro_ag_ids` are unique within the step.
- `micro_ag_ids` are ordered lexicographically ascending.
- A MAG appears in exactly one deployment step in a successful response.

## Entity: DeploymentSequence

Represents the deployment plan derived from the reduced graph.

### Fields

- **`bypassed_edges`** (array of `MicroAgDependencyEdge`, required): Edges removed from the
  resolved graph for cycle handling.
- **`steps`** (array of `DeploymentStep`, required): Ordered deployment layers.

### Generation Rules

- `bypassed_edges` are populated only when cycles are detected.
- Each step contains every MAG with no remaining outgoing dependency edges in the reduced graph.
- When multiple MAGs are deployable in the same layer, they are grouped into the same step.

## Entity: DeploymentScopeResponse

Represents the full endpoint response.

### Fields

- **`micro_ag_id`** (string, required): Requested root MAG identifier.
- **`environment`** (string, required): Requested environment.
- **`effective_date`** (string, required): UTC generation timestamp in Zulu format.
- **`graph_has_cycles`** (boolean, required): Whether the resolved graph required cycle bypass.
- **`dependency_graph`** (array of `MicroAgDependencyEdge`, required): Full resolved edge set,
  including any cycle-marked back-edge.
- **`deployment_sequence`** (`DeploymentSequence`, required): Reduced DAG deployment order.

### Validation Rules

- All response fields are snake_case.
- `effective_date` reflects generation time, not source-document storage time.
- `dependency_graph` is deduplicated and ordered lexicographically.
- The response remains valid when `dependency_graph` is empty; in that case
  `deployment_sequence.steps` still contains the root MAG in step 1.

## Supporting Entity: WorkloadOwnershipMatch

Represents a derived match from a destination workload asset to a target processed MAG.

### Fields

- **`asset_id`** (string, required): Destination workload asset identifier.
- **`target_micro_ag_id`** (string, required): MAG that owns the workload.
- **`environment`** (string, required): Requested environment used for the match.

### Rules

- A successful join yields at most one target MAG per asset within an environment.
- Zero matches for a required downstream join trigger a graph-resolution failure.
- More than one match for a required downstream join trigger an ambiguous graph-resolution
  failure.

## State Transitions / Resolution Flow

- **Missing root -> 404**: No processed source document exists for `(micro_ag_id, environment)`.
- **Root found -> resolved scope**: The system includes the root MAG, resolves exactly one inverse
  upstream hop, then expands downstream one hop at a time up to 30 hops.
- **Resolved scope -> reduced DAG**: The system detects cycles, marks the selected back-edge(s) as
  cyclic in the full graph, removes them from the reduced graph, and computes deployment layers.
- **Resolved scope with broken downstream join -> 422**: Any required downstream asset-to-MAG join
  that is missing, malformed, or ambiguous after the root is found fails the request.
- **Reduced DAG -> successful response**: The system returns a generated deployment-scope response
  and persists nothing.

## Bounded Traversal Behavior

- Downstream expansion is capped at 30 hops.
- Nodes and edges discovered within the first 30 hops are retained.
- Traversal stops cleanly at the boundary; the design does not require including hop-31 nodes.
- Cycle detection and deployment sequencing apply only to the resolved scope within the 30-hop
  boundary.