# Quickstart: Micro Affinity Group Submission

**Branch**: 007-add-micro-affinity-endpoint  
**Date**: 2026-05-05

This quickstart verifies that `POST /micro-affinity-groups` validates a micro affinity group
payload, checks each workload against the matching application architecture document, and upserts
the payload into MongoDB keyed by `micro-ag-id + environment + architecture-version`.

## Prerequisites

- Python 3.12+
- Docker (recommended for local MongoDB)

## Run MongoDB locally

```bash
docker run --rm -p 27017:27017 --name graph-service-mongo mongo:7
```

## Run the service

```bash
cd /Users/ertant/work/vscode-projects/graph-service
uvicorn src.infrastructure.main:create_app --factory --reload --port 8000
```

## Seed the matching application architecture

```bash
cat > /tmp/application-architecture-mag.json <<'JSON'
{
  "metadata": {
    "AssetID": "ba0270",
    "version": "1.0.0",
    "created": "2026-05-05"
  },
  "nodes": [
    {
      "unique-id": "pq0177",
      "node-type": "service",
      "name": "RW Orchestrator",
      "description": "Service backing workload 1",
      "metadata": {
        "code-repo": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
        "asset-id": "pq0177"
      }
    },
    {
      "unique-id": "dh6980",
      "node-type": "service",
      "name": "RW CAP Service",
      "description": "Service backing workload 2",
      "metadata": {
        "code-repo": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
        "asset-id": "dh6980"
      }
    }
  ],
  "relationships": []
}
JSON

curl -i -sS -X POST http://localhost:8000/application-architectures \
  -H 'content-type: application/json' \
  --data-binary @/tmp/application-architecture-mag.json
```

Expected:

- Status: `201 Created`
- Response body equals the stored application architecture document

## Create a valid micro affinity group request body

```bash
cat > /tmp/micro-affinity-group.json <<'JSON'
{
  "micro-ag-id": "mAG_A",
  "name": "Micro Affinity Group A",
  "parent-asset-id": "ba0270",
  "architecture-version": "1.0.0",
  "environment": "production",
  "effective-date": "2025-01-01T14:00:00Z",
  "workloads": [
    {
      "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
      "asset-id": "pq0177"
    },
    {
      "id": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
      "asset-id": "dh6980"
    }
  ]
}
JSON
```

## First request (expected 201)

```bash
curl -i -sS -X POST http://localhost:8000/micro-affinity-groups \
  -H 'content-type: application/json' \
  --data-binary @/tmp/micro-affinity-group.json
```

Expected:

- Status: `201 Created`
- Response body equals the stored micro affinity group document

## Second request with the same unique key (expected 200)

```bash
curl -i -sS -X POST http://localhost:8000/micro-affinity-groups \
  -H 'content-type: application/json' \
  --data-binary @/tmp/micro-affinity-group.json
```

Expected:

- Status: `200 OK`
- Response body equals the stored micro affinity group document

## Verify the record in MongoDB

```bash
mongosh "mongodb://localhost:27017/graph_service" \
  --eval 'db.getCollection("micro-affinity-groups").find({"micro-ag-id":"mAG_A","environment":"production","architecture-version":"1.0.0"}).pretty()'
```

Expected:

- Exactly one document exists for `mAG_A` in `production` at architecture version `1.0.0`
- The stored document matches the latest submitted payload

## Invalid semver example (expected 422)

```bash
cat > /tmp/micro-affinity-group-invalid-version.json <<'JSON'
{
  "micro-ag-id": "mAG_A",
  "parent-asset-id": "ba0270",
  "architecture-version": "v1.0.0",
  "environment": "production",
  "effective-date": "2025-01-01T14:00:00Z",
  "workloads": [
    {
      "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
      "asset-id": "pq0177"
    }
  ]
}
JSON

curl -i -sS -X POST http://localhost:8000/micro-affinity-groups \
  -H 'content-type: application/json' \
  --data-binary @/tmp/micro-affinity-group-invalid-version.json
```

Expected:

- Status: `422 Unprocessable Entity`
- Response content-type: `application/problem+json`

## Invalid effective-date example (expected 422)

```bash
cat > /tmp/micro-affinity-group-invalid-date.json <<'JSON'
{
  "micro-ag-id": "mAG_A",
  "parent-asset-id": "ba0270",
  "architecture-version": "1.0.0",
  "environment": "production",
  "effective-date": "2025-01-01",
  "workloads": [
    {
      "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
      "asset-id": "pq0177"
    }
  ]
}
JSON

curl -i -sS -X POST http://localhost:8000/micro-affinity-groups \
  -H 'content-type: application/json' \
  --data-binary @/tmp/micro-affinity-group-invalid-date.json
```

Expected:

- Status: `422 Unprocessable Entity`
- Response content-type: `application/problem+json`

## Invalid workload lookup example (expected 422)

```bash
cat > /tmp/micro-affinity-group-invalid-workload.json <<'JSON'
{
  "micro-ag-id": "mAG_A",
  "parent-asset-id": "ba0270",
  "architecture-version": "1.0.0",
  "environment": "production",
  "effective-date": "2025-01-01T14:00:00Z",
  "workloads": [
    {
      "id": "AIMC/repos/does-not-exist",
      "asset-id": "pq0177"
    }
  ]
}
JSON

curl -i -sS -X POST http://localhost:8000/micro-affinity-groups \
  -H 'content-type: application/json' \
  --data-binary @/tmp/micro-affinity-group-invalid-workload.json
```

Expected:

- Status: `422 Unprocessable Entity`
- Response content-type: `application/problem+json`

## Notes

- The planning-time contract working copy lives at
  `specs/007-add-micro-affinity-endpoint/contracts/micro_affinity_group.schema.json`.
- Implementation is expected to promote the final authoritative codegen source into
  `specs/001-service-skeleton/contracts/` and then refresh generated inbound models via
  `./generate_inbound_models.sh`.
- Cross-collection validation failures are expected to surface as `422 application/problem+json`
  through mapped domain exceptions rather than inbound schema validation.
- Workload validation compares the submitted `workload.asset-id` against the resolved service
  node `metadata.asset-id` for the matching `metadata.code-repo`.