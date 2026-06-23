# HTTP API Contract Delta: Deploy-Scope Graph Resolution Fix

## Endpoint

`GET /v1/micro-affinity-groups/{id}/deployment-scope?environment={environment}`

## Contract Status

- Request contract: unchanged
- Response schema shape: unchanged
- Error semantics: unchanged (`404` missing root path resource; `422` downstream resolution
  failure after root exists)

## Behavioral Corrections

1. Graph resolution seeds downstream traversal from immediate one-hop upstream dependents of the
   requested root MAG (fallback to root when upstream set is empty).
2. Cycle detection marks an edge as cyclic only when the destination is already present in the
   current traversal path (path back-edge rule).
3. Any cyclic edge is:
   - returned in `dependency_graph` with `is_cyclic: true`
   - mirrored in `deployment_sequence.bypassed_edges`
   - excluded from deployment-step topological calculation
4. Deployment-step algorithm remains unchanged aside from consuming the reduced graph.

## Ordering Contract

- `dependency_graph`: non-cyclic edges first then cyclic edges, both segments lexicographically
  sorted by `(source_micro_ag_id, destination_micro_ag_id)`.
- `deployment_sequence.steps`: ordered by `step_index` ascending.
- `deployment_sequence.steps[*].micro_ag_ids`: lexicographically ascending.

## Required Example Behaviors

### Root `C`

The response behavior must match the specification's expected output for root `C`, including:

- complete edge inclusion for one-hop-upstream-seeded downstream traversal
- expected cyclic edge classification
- expected `bypassed_edges`
- expected deterministic step layering

### Root `E3`

The response behavior must match the specification's expected output for root `E3`, including:

- complete edge inclusion
- expected cyclic edge classification
- expected `bypassed_edges`
- expected deterministic step layering

## Non-Goals

- No endpoint rename or alias changes.
- No field additions/removals/renames in response schema.
- No canonical schema migration under `schemas/`.
