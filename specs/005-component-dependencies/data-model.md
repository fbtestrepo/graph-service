# Data Model: Component Dependencies Graph

**Branch**: 005-component-dependencies  
**Date**: 2026-03-26

## Overview

This feature adds a new read-only endpoint that returns a transitive dependency graph for a root component node.

- **Input**: a root `node-id`
- **Output**: an edge list response describing all reachable upstream and downstream relationships, subject to:
  - cycle stopping (but cycle edges included)
  - maximum traversal depth of 20 hops

The response format is node-level edges, derived from interface-level relationship records stored in component-node payloads.

## Stored Data: ComponentNodeDocument (MongoDB)

### Collection

- **Collection**: `components`

### Stored Shape

- Documents match the component-node payload schema (see `component_node.schema.json`).
- Relationship records (if present) live under `relationships[]` and use:
  - `relationship-type`
  - `source.node-id`, `source.interface-local-id`
  - `target.node-id`, `target.interface-local-id`

### Edge Extraction Rule

Each stored relationship contributes one directed dependency edge:

- `relationship-type` → same value as stored
- `source-node-id` → `relationships[i].source.node-id`
- `target-node-id` → `relationships[i].target.node-id`

Interface-local-id values are used for defining relationships in the stored payload but are not included in the dependency edge list response.

## Response Entity: ComponentDependenciesResponse (API)

### Fields

- **`node-id`** (string, required, non-empty): the requested root node.
- **`dependency-graph`** (array, required): list of dependency edges.

### Edge: DependencyEdge

- **`relationship-type`** (string, required, non-empty)
- **`source-node-id`** (string, required, non-empty)
- **`target-node-id`** (string, required, non-empty)

### Validation Rules (Boundary)

- `node-id` path parameter must be a non-empty string (routing/path validation).
- `404 Not Found` if the root node-id does not exist.

## Traversal Model

### Reachability

The returned graph includes all edges reachable from the root under both:

- **Downstream** traversal: follow edges `source-node-id → target-node-id`.
- **Upstream** traversal: follow edges in reverse direction, i.e. discover edges where `target-node-id == current`.

### Depth Limit

- Maximum hop distance from the root is 20.
- Expansion stops beyond this limit (edges discovered within the explored boundary are returned; no further expansion is performed).

### Cycle Handling

- Cycles are detected via visited node tracking.
- Edges that close cycles are included, but nodes already expanded are not expanded again.

### Deduplication and Ordering

- Unique edge identity is `(relationship-type, source-node-id, target-node-id)`.
- The response edge list is deterministic: sort by `relationship-type`, then `source-node-id`, then `target-node-id`.

## Port Implications (Core)

To support upstream traversal efficiently, core requires a port capability to find relationship edges incident to a set of node-ids without scanning the entire collection.

A suitable port method can return edges that match either:

- `relationships.source.node-id ∈ frontier`
- `relationships.target.node-id ∈ frontier`

This method is implemented by the outbound MongoDB adapter.
