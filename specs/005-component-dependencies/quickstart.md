# Quickstart: Component Dependencies

**Branch**: 005-component-dependencies  
**Date**: 2026-03-26

This quickstart verifies that `GET /components/{node-id}/dependencies` returns a full transitive dependency graph (upstream + downstream) as a stable edge list.

## Prerequisites

- Python 3.12+
- Docker (recommended for running MongoDB locally)

## Run MongoDB locally

```bash
docker run --rm -p 27017:27017 --name graph-service-mongo mongo:7
```

## Run the service

```bash
cd /Users/ertant/work/vscode-projects/graph-service
uvicorn src.infrastructure.main:create_app --factory --reload --port 8000
```

## Seed sample component nodes

This seeds a small graph with both downstream and upstream edges around `mAG_A`:

- Downstream chain: `mAG_A -> mAG_B -> mAG_C -> mAG_D`
- Upstream edge: `mAG_X -> mAG_A`

### Create/Upsert mAG_A (uses existing sample file)

```bash
curl -i -sS -X POST http://localhost:8000/components \
  -H 'content-type: application/json' \
  --data-binary @specs/sample-component-payload/sample-mag.json
```

### Create/Upsert mAG_B

```bash
curl -i -sS -X POST http://localhost:8000/components \
  -H 'content-type: application/json' \
  --data-binary @- <<'JSON'
{
  "node-id": "mAG_B",
  "node-type": "micro-affinity-group",
  "node-name": "Micro Affinity Group B",
  "metadata": {"parent-asset-id": "ba0270"},
  "interfaces": [{"interface-local-id": "workload_1", "interface-type": "workload"}],
  "relationships": [
    {
      "relationship-type": "depends-on",
      "source": {"node-id": "mAG_B", "interface-local-id": "workload_1"},
      "target": {"node-id": "mAG_C", "interface-local-id": "workload_1"}
    }
  ]
}
JSON
```

### Create/Upsert mAG_C

```bash
curl -i -sS -X POST http://localhost:8000/components \
  -H 'content-type: application/json' \
  --data-binary @- <<'JSON'
{
  "node-id": "mAG_C",
  "node-type": "micro-affinity-group",
  "node-name": "Micro Affinity Group C",
  "metadata": {"parent-asset-id": "ba0270"},
  "interfaces": [{"interface-local-id": "workload_1", "interface-type": "workload"}],
  "relationships": [
    {
      "relationship-type": "depends-on",
      "source": {"node-id": "mAG_C", "interface-local-id": "workload_1"},
      "target": {"node-id": "mAG_D", "interface-local-id": "workload_1"}
    }
  ]
}
JSON
```

### Create/Upsert mAG_X (upstream reference to mAG_A)

```bash
curl -i -sS -X POST http://localhost:8000/components \
  -H 'content-type: application/json' \
  --data-binary @- <<'JSON'
{
  "node-id": "mAG_X",
  "node-type": "micro-affinity-group",
  "node-name": "Micro Affinity Group X",
  "metadata": {"parent-asset-id": "ba0270"},
  "interfaces": [{"interface-local-id": "workload_1", "interface-type": "workload"}],
  "relationships": [
    {
      "relationship-type": "depends-on",
      "source": {"node-id": "mAG_X", "interface-local-id": "workload_1"},
      "target": {"node-id": "mAG_A", "interface-local-id": "workload_1"}
    }
  ]
}
JSON
```

## Call the dependencies endpoint

```bash
curl -i -sS http://localhost:8000/components/mAG_A/dependencies
```

Expected:
- Status: `200 OK`
- Response body contains (at least) these four edges (order is deterministic and sorted):
  - `mAG_A -> mAG_B`
  - `mAG_B -> mAG_C`
  - `mAG_C -> mAG_D`
  - `mAG_X -> mAG_A`

## Missing root node

```bash
curl -i -sS http://localhost:8000/components/does-not-exist/dependencies
```

Expected:
- Status: `404 Not Found`
- Response content-type: `application/problem+json`

If the root node exists but a required downstream traversal record is missing or otherwise
unresolvable, the endpoint must return:

- Status: `422 Unprocessable Entity`
- Body: Problem Details payload indicating downstream graph resolution failed after root existence
  was confirmed.
