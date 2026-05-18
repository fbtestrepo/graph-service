# HTTP API: MAG Deployment Scope

## GET /v1/micro-affinity-groups/{id}/deployment-scope

Returns a deployment-scope projection for one processed Micro-AG in one environment.

### Path and query parameters

- `id` (string, required): Root `micro_ag_id` to resolve.
- `environment` (string, required, query): Environment scope for root lookup and all downstream
  joins.

### Semantics

- The root MAG is looked up in `micro_affinity_groups_processed` by `(micro_ag_id, environment)`.
- The resolved graph always includes the root MAG.
- Upstream traversal is limited to exactly one inverse hop from the root.
- Downstream traversal continues one hop at a time until no new MAGs are found or the 30-hop
  boundary is reached.
- Workload-level destination relationships are matched to target MAGs by `asset_id` ownership in
  the same environment.
- Internal source-to-destination relationships inside the same MAG do not emit self edges.
- The full `dependency_graph` includes any cycle-completing back-edge flagged with
  `is_cyclic: true`.
- `deployment_sequence` is computed from the reduced DAG after bypassing the selected cycle edges.

### Responses

- `200 OK`: Deployment scope returned.
- `404 Not Found`: The requested `(micro_ag_id, environment)` root pair does not exist.
- `422 Unprocessable Entity`: The root exists but required downstream graph resolution is missing,
  malformed, or ambiguous.
- `500 Internal Server Error`: Unhandled infrastructure failure.

### Response body

Success responses use `application/json` and conform to `deployment_scope_response.schema.json`.
The executable sample at `specs/samples/micro-affinity-group/deployment-scope.json` remains the
runtime source of truth for snake_case naming, edge ordering, and deployment-step ordering.
The runtime response model is generated into
`src/adapters/inbound/api/schemas/micro_affinity_group_deployment_scope.py` via
`generate_inbound_models.sh`, with companion generated modules for steps, sequences, and edges in
the same schema package.

Error responses use `application/problem+json` and conform to the shared
`problem_details.schema.json` contract.