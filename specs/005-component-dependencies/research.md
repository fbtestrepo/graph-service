# Research: Component Dependencies Graph

**Branch**: 005-component-dependencies  
**Date**: 2026-03-26

## Decisions

### Decision 1: Represent dependencies as a node-level edge list

- **Decision**: The dependencies endpoint returns an edge list with fields:
  - `relationship-type`
  - `source-node-id`
  - `target-node-id`

  matching `specs/sample-component-dependencies/sample-mag-dependencies.json`.
- **Rationale**:
  - Matches the provided sample output and keeps the response small and stable.
  - Although relationships are expressed between interfaces in stored payloads, the requested output is node-level.
- **Alternatives considered**:
  - Include interface-local-id in the output: rejected because the example output is node-level and the feature request explicitly points to that shape.

### Decision 2: Traverse one hop at a time with a depth cap of 20

- **Decision**: Compute the transitive graph via level-order expansion (BFS) and stop expanding beyond 20 hops from the root.
- **Rationale**:
  - Matches the requirement to build the graph one hop at a time.
  - The depth cap bounds worst-case work and prevents runaway traversals.
- **Alternatives considered**:
  - Unbounded traversal: rejected due to risk of large graphs and pathological cycles.
  - DFS: rejected because the requirement explicitly suggests hop-by-hop expansion.

### Decision 3: Cycle handling returns the cycle edge but stops expanding

- **Decision**: Maintain:
  - `visited_nodes` to prevent re-expansion of already-seen nodes
  - `seen_edges` to prevent duplicates

  Always include a newly discovered edge (if not already in `seen_edges`), even if it targets an already visited node. Only enqueue a node for further expansion if it is not yet visited and the next depth is within the limit.
- **Rationale**:
  - Includes cycle-closing edges such as A → B → C → A.
  - Prevents infinite loops.
- **Alternatives considered**:
  - Drop edges that point to visited nodes: rejected because it would omit the cycle edge.

### Decision 4: Upstream traversal requires reverse-edge lookup via a port method

- **Decision**: Extend the core component-node repository port to support finding relationship edges where a node-id appears as either:
  - `relationships.source.node-id` (downstream edges)
  - `relationships.target.node-id` (upstream edges)

  ideally with batch `$in` queries to support “frontier” expansion.
- **Rationale**:
  - Downstream edges can be derived from reading each node’s stored payload.
  - Upstream edges cannot be derived without a reverse lookup (otherwise it requires scanning all documents).
  - The reverse lookup must remain outside core (port + Mongo adapter) per constitution.
- **Alternatives considered**:
  - Full collection scan for upstream edges: rejected due to poor scalability.

### Decision 5: Deterministic output ordering

- **Decision**: After traversal, sort edges by:
  1) `relationship-type`
  2) `source-node-id`
  3) `target-node-id`

  all ascending lexical order.
- **Rationale**:
  - Produces stable output suitable for tests and automation.
- **Alternatives considered**:
  - Preserve discovery order: rejected because Mongo iteration order and traversal order are less predictable.

## Notes

- This feature uses stored relationship data originating from component-node payloads submitted to `POST /components`.
- If performance becomes an issue, add MongoDB indexes on `relationships.source.node-id` and `relationships.target.node-id` as a follow-up optimization.
