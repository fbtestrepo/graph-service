# HTTP API Contract Delta: Fix MAG Cycle Detection

## Endpoint

`GET /v1/micro-affinity-groups/{id}/deployment-scope?environment={environment}`

## Contract Status

- Request contract: unchanged
- Response schema shape: unchanged
- Error semantics: unchanged

## Behavioral Correction

For cyclic graphs, the endpoint must mark as cyclic only those MAG edges whose destination MAG is
already present earlier on the active root-scoped traversal path used to resolve deployment scope.

## Corrected Example For Root `C`

For the graph:

- `A -> C`
- `B -> C`
- `C -> D`
- `D -> E`
- `F -> E`
- `G -> F`
- `E -> E1`
- `E -> E2`
- `E -> E3`
- `E1 -> C`

The corrected behavior is:

- `dependency_graph` keeps `C -> D` as a normal non-cyclic edge
- `dependency_graph` marks `E1 -> C` with `is_cyclic = true`
- `deployment_sequence.bypassed_edges` contains only `E1 -> C`
- `deployment_sequence.steps` are:
  - step 1: `E1`, `E2`, `E3`
  - step 2: `E`
  - step 3: `D`
  - step 4: `C`
  - step 5: `A`, `B`

## Non-Goals

- No new fields are introduced.
- No existing fields are removed or renamed.
- No behavior changes are intended for acyclic graphs.
- No changes are intended to `404` versus `422` semantics.