# HTTP API Contract: Workload Test Scope Endpoint

## Endpoint

`POST /v1/micro-affinity-groups/workloads/test-scope?environment={environment}`

Purpose: Return environment-scoped impacted workload relationships and summary statistics for the
provided changed workload asset IDs.

## Media Types

- Success responses: `application/json`
- Error responses: `application/problem+json` (RFC 7807)

## Request Contract

- Query parameter:
  - `environment` (string, required)
- Body:

```json
{
  "changed_workloads": [
    { "workload_asset_id": "asset_id_1" },
    { "workload_asset_id": "asset_id_2" }
  ]
}
```

### Request Validation

- `environment` is required and must be non-empty.
- Missing or blank `environment` returns `422` and no processing is executed.
- `changed_workloads` accepts an empty list.
- Input IDs are deduplicated by first-seen order for processing.

## Success Response Contract (`200 OK`)

Response shape (snake_case keys only):

```json
{
  "timestamp": "2026-06-12T10:30:00Z",
  "environment": "preproduction",
  "changed_workloads": [
    {
      "workload_asset_id": "asset_1",
      "micro_ag_id": "mAG_A"
    }
  ],
  "affected_workload_relationships": [
    {
      "source_workload": {
        "workload_asset_id": "asset_1",
        "micro_ag_id": "mAG_A"
      },
      "destination_workload": {
        "workload_asset_id": "asset_2",
        "micro_ag_id": "mAG_B"
      }
    }
  ],
  "unknown_workloads": [
    {
      "workload_asset_id": "unknown_asset_id"
    }
  ],
  "summary": {
    "total_affected_workload_relationships": 1,
    "total_affected_workloads": 2,
    "total_affected_micro_ags": 2,
    "total_unknown_workloads": 1
  }
}
```

### Success Semantics

- Relationship resolution uses only records in the requested `environment`.
- Both matching directions are included:
  - changed workload as relationship source
  - changed workload as relationship destination
- `affected_workload_relationships` is deduplicated and sorted lexicographically by
  `(source_workload.workload_asset_id, destination_workload.workload_asset_id)`.
- Unresolved relationship candidates are excluded and unresolved endpoint IDs are added to
  `unknown_workloads`.
- Ambiguous workload ownership behavior is defined in Error Responses (`422`).
- If environment has no records:
  - status remains `200`
  - `changed_workloads` is empty
  - `affected_workload_relationships` is empty
  - `unknown_workloads` contains all deduplicated input IDs in first-seen order

## Error Responses

- `400 application/problem+json`: malformed/unparseable JSON body.
- `422 application/problem+json`: validation failures (including missing/blank `environment`) and
  ambiguous workload ownership in environment-scoped resolution.
- `500 application/problem+json`: unhandled infrastructure failures.

## Contract References

- Output example source: `specs/samples/micro-affinity-group/workload/test-scope.json`
- Relationship sample source: `specs/samples/micro-affinity-group/micro-affinity-group-relationships.json`
