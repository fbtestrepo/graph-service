# Data Model: Fix MAG Cycle Detection

## Overview

This feature corrects how the existing deployment-scope model identifies cyclic edges and derives
deployment stages for cyclic graphs. The request and response schema remain unchanged; the logical
entities below describe the corrected internal behavior.

## Entity: RootScopedTraversalPath

Represents the ordered MAG path followed while resolving deployment scope for a single root MAG
after the one-hop-upstream boundary is established.

### Fields

- **`root_micro_ag_id`** (string, required): The requested deployment-scope root MAG.
- **`environment`** (string, required): Environment scope for traversal.
- **`path_micro_ag_ids`** (ordered array of string, required): MAG identifiers on the current
  active traversal path.

### Validation Rules

- The path begins with the requested root MAG or a one-hop-upstream consumer path that terminates
  at the root.
- A MAG may appear only once on the active path before a back-edge is detected.

## Entity: ResolvedDependencyEdge

Represents one MAG-to-MAG dependency edge discovered during deployment-scope traversal.

### Fields

- **`source_micro_ag_id`** (string, required): MAG that depends on another MAG.
- **`destination_micro_ag_id`** (string, required): MAG that must deploy before the source MAG.
- **`is_cyclic`** (boolean, optional): Present only when the edge is identified as a path-scoped
  cyclic back-edge.

### Validation Rules

- Edge uniqueness remains the pair `(source_micro_ag_id, destination_micro_ag_id)`.
- An edge is cyclic only if `destination_micro_ag_id` already appears earlier on the current
  active traversal path.
- Non-cyclic edges remain eligible for deployment-stage calculation.

## Entity: PathScopedCycleEdge

Represents a resolved dependency edge excluded from deployment-stage calculation because it closes a
cycle on the active traversal path.

### Fields

- **`source_micro_ag_id`** (string, required)
- **`destination_micro_ag_id`** (string, required)

### Validation Rules

- Every path-scoped cycle edge must also exist in `dependency_graph` with `is_cyclic = true`.
- Every path-scoped cycle edge must appear in `deployment_sequence.bypassed_edges`.

## Entity: ReducedDeploymentGraph

Represents the resolved dependency graph after excluding all path-scoped cycle edges from
deployment-stage calculation.

### Generation Rules

- Starts from the full `dependency_graph`.
- Removes only the edges listed in `deployment_sequence.bypassed_edges`.
- Preserves all non-cyclic branches and upstream consumer edges.

## Entity: DeploymentStage

Represents one ordered execution step in the deployment sequence derived from the reduced graph.

### Fields

- **`step_index`** (integer, required): One-based deployment stage index.
- **`micro_ag_ids`** (array of string, required): MAGs deployable in parallel at this stage.

### Validation Rules

- `micro_ag_ids` are unique within the stage.
- `micro_ag_ids` remain ordered deterministically.
- A MAG appears in exactly one deployment stage in a successful response.

## Expected State Transition For The Reported Graph

1. The root-scoped traversal for `C` resolves upstream consumers `A` and `B`, then downstream path
   `C -> D -> E -> E1` plus parallel branches `E -> E2` and `E -> E3`.
2. The edge `E1 -> C` is identified as cyclic because `C` already exists earlier on that active
   traversal path.
3. `E1 -> C` remains in `dependency_graph` and is flagged with `is_cyclic = true`.
4. `E1 -> C` is copied into `deployment_sequence.bypassed_edges`.
5. Deployment stages are computed from the graph after excluding only `E1 -> C`.