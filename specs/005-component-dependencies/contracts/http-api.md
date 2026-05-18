# HTTP API: Component Dependencies

## GET /components/{node_id}/dependencies

Returns the transitive dependency graph for the component identified by `{node_id}`.

### Semantics

- Returns **both** downstream and upstream dependencies.
- Traverses **one hop at a time** (level-order) and stops expanding beyond **20 hops**.
- Boundary rule at depth 20: may fetch/include edges incident to depth-20 nodes only when both endpoints are already within ≤ 20 hops from the root; must not include edges that would introduce hop-21 nodes; must not expand beyond depth 20.
- Handles cycles by **including cycle-closing edges** but stopping infinite traversal.
- Filters to “self-sourced” relationships only (only include relationships where `relationship.source.node-id == document.node-id`).
- Returns a **deduplicated**, deterministic edge list ordered by `relationship-type`, then `source-node-id`, then `target-node-id`.

### Path parameters

- `node_id` (string, required): root node id.

### Responses

- `200 OK`: `ComponentDependenciesResponse`
- `404 Not Found`: root node-id does not exist
- `422 Unprocessable Entity`: root node exists but downstream graph resolution fails because a
  required intermediate or dependent record cannot be resolved consistently
- `500 Internal Server Error`: unexpected failure

### Response schema

See `component_dependencies_response.schema.json`.

### Example

```json
{
  "node-id": "mag",
  "dependency-graph": [
    {
      "relationship-type": "depends-on",
      "source-node-id": "mag",
      "target-node-id": "sia"
    }
  ]
}
```
