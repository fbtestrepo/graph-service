# Data Model: Deploy-Scope Graph Resolution Fix

## Overview

This feature is a behavior correction over existing deploy-scope contracts. Request/response schema
shape is unchanged; model updates are in traversal semantics, cycle labeling, and ordering.

## Entity: TraversalSeedSet

Defines traversal initialization context for one request.

### Fields

- **`root_micro_ag_id`** (string, required): Requested MAG from the path.
- **`upstream_seed_micro_ag_ids`** (set of string, required): Immediate one-hop upstream
  dependents of `root_micro_ag_id`.
- **`effective_seed_micro_ag_ids`** (ordered set of string, required):
  `upstream_seed_micro_ag_ids` when non-empty, otherwise `{root_micro_ag_id}`.

### Validation Rules

- `upstream_seed_micro_ag_ids` includes only one-hop upstream dependents (no recursion).
- If upstream seed set is empty, effective seed set contains exactly root.

## Entity: BranchTraversalPath

Represents branch-local traversal state used for cycle classification.

### Fields

- **`path_micro_ag_ids`** (ordered array of string, required): Current DFS branch path state.
- **`initialized_with_root`** (boolean, required): Always true.
- **`initialized_with_one_hop_upstream`** (boolean, required): True when upstream seeds exist.

### Validation Rules

- Initial path content must include root and all immediate upstream dependents discovered for the
  request.
- Path updates are branch-local; sibling branches do not mutate each other's path state.

## Entity: ResolvedDependencyEdge

Represents an edge in `dependency_graph`.

### Fields

- **`source_micro_ag_id`** (string, required)
- **`destination_micro_ag_id`** (string, required)
- **`is_cyclic`** (boolean, optional): Present and true only for path-scoped back-edges.

### Validation Rules

- Edge identity is unique by `(source_micro_ag_id, destination_micro_ag_id)`.
- `is_cyclic = true` iff destination already exists on current `BranchTraversalPath`.

## Entity: BypassedEdge

Represents a cycle edge excluded from topological deployment-step calculations.

### Fields

- **`source_micro_ag_id`** (string, required)
- **`destination_micro_ag_id`** (string, required)

### Validation Rules

- Every `BypassedEdge` must correspond to one `ResolvedDependencyEdge` with `is_cyclic = true`.
- Only `BypassedEdge` entries are excluded from step layering.

## Entity: ReducedDeploymentGraph

Graph used for deployment step calculation.

### Generation Rules

- Start from full deduplicated `dependency_graph`.
- Remove only edges in `deployment_sequence.bypassed_edges`.
- Keep all remaining non-cyclic edges.

## Entity: DeploymentStep

One deployment layer in `deployment_sequence.steps`.

### Fields

- **`step_index`** (integer, required): 1-based contiguous index.
- **`micro_ag_ids`** (array of string, required): Parallel-deployable MAGs.

### Validation Rules

- `step_index` values strictly increase by 1.
- `micro_ag_ids` are unique and sorted lexicographically within each step.
- A MAG appears in at most one step.

## Ordering Contract Model

- `dependency_graph`: non-cyclic edges first, then cyclic edges; each segment sorted
  lexicographically by `(source_micro_ag_id, destination_micro_ag_id)`.
- `deployment_sequence.steps`: sorted by `step_index` ascending.
- `deployment_sequence.steps[*].micro_ag_ids`: lexicographically ascending.

## State Transition Notes

1. Resolve one-hop upstream seed set for requested root.
2. Initialize branch traversal path with root + one-hop upstream dependents.
3. Traverse downstream from effective seed set and emit deduplicated edges.
4. Mark edges as cyclic only on path back-edge condition.
5. Copy cyclic edges to `bypassed_edges` and exclude only these from layering.
6. Produce ordered deployment steps from reduced graph.
