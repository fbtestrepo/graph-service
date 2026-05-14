# Quickstart: Micro Affinity Group Relationship Enrichment

**Branch**: 008-add-mag-relationships  
**Date**: 2026-05-06

This quickstart verifies that `POST /micro-affinity-groups` preserves the raw submission,
generates relationship entries from application architecture edges, and stores the transformed
document in `micro-affinity-groups-processed` within one transaction.

## Prerequisites

- Python 3.12+
- Docker
- MongoDB deployment configured as a replica set for transaction support

## Run MongoDB locally as a single-node replica set

```bash
docker run --rm -d -p 27017:27017 --name graph-service-mongo mongo:7.0 --replSet rs0 --bind_ip_all
docker exec graph-service-mongo mongosh --eval 'rs.initiate({_id:"rs0",members:[{_id:0,host:"127.0.0.1:27017"}]})'
```

Use a URI that includes the replica set name, for example:

```bash
export GRAPH_SERVICE_MONGODB_URI='mongodb://127.0.0.1:27017/?replicaSet=rs0'
export GRAPH_SERVICE_MONGODB_DATABASE='graph_service'
```

## Run the service

```bash
cd /Users/ertant/work/vscode-projects/graph-service
./generate_inbound_models.sh
uvicorn src.infrastructure.main:create_app --factory --reload --port 8000
```

## Seed an application architecture with one outgoing service relationship

```bash
cat > /tmp/application-architecture-mag-relationships.json <<'JSON'
{
  "metadata": {
    "AssetID": "ba0270",
    "version": "1.0.0",
    "created": "2026-05-06"
  },
  "nodes": [
    {
      "unique-id": "service-pq0177",
      "node-type": "service",
      "name": "RW Orchestrator",
      "description": "Service backing workload 1",
      "metadata": {
        "code-repo": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
        "asset-id": "pq0177"
      }
    },
    {
      "unique-id": "service-dh6980",
      "node-type": "service",
      "name": "RW CAP Service",
      "description": "Service backing workload 2",
      "metadata": {
        "code-repo": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
        "asset-id": "dh6980"
      }
    }
  ],
  "relationships": [
    {
      "unique-id": "rel-service-pq0177-to-service-dh6980",
      "relationship-type": {
        "connects": {
          "source": {
            "node": "service-pq0177"
          },
          "destination": {
            "node": "service-dh6980"
          }
        }
      }
    }
  ]
}
JSON

curl -i -sS -X POST http://localhost:8000/application-architectures \
  -H 'content-type: application/json' \
  --data-binary @/tmp/application-architecture-mag-relationships.json
```

Expected:

- Status: `201 Created`

## Submit a valid micro affinity group document

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

curl -i -sS -X POST http://localhost:8000/micro-affinity-groups \
  -H 'content-type: application/json' \
  --data-binary @/tmp/micro-affinity-group.json
```

Expected:

- Status: `201 Created`
- Response body includes the original fields plus:

```json
"relationships": [
  {
    "source-workload": {
      "id": "AIMC/repos/rw-orchestrator-svc_ba0116_pq0177",
      "asset-id": "pq0177"
    },
    "destination-workload": {
      "id": "AIMC/repos/rw-cap-svc_ba0116_dh6980",
      "asset-id": "dh6980"
    }
  }
]
```

## Verify raw and processed records

```bash
mongosh "$GRAPH_SERVICE_MONGODB_URI/$GRAPH_SERVICE_MONGODB_DATABASE" \
  --eval 'db.getCollection("micro-affinity-groups").find({"micro-ag-id":"mAG_A"}).pretty()'

mongosh "$GRAPH_SERVICE_MONGODB_URI/$GRAPH_SERVICE_MONGODB_DATABASE" \
  --eval 'db.getCollection("micro-affinity-groups-processed").find({"micro-ag-id":"mAG_A"}).pretty()'
```

Expected:

- Raw collection contains the original request shape without `relationships`
- Processed collection contains the transformed document with `relationships`
- Both documents share the same composite identity fields

## Zero-relationship case

Update the seeded architecture so the source service has no outgoing relationship edges, then send
the same request again.

Expected:

- Status: `200 OK` for the same composite key
- Processed document contains `"relationships": []`

## Dangling destination case

Modify the architecture relationship to point to a non-existent destination `unique-id`, then
submit the request again.

Expected:

- Status: `422 Unprocessable Entity`
- Neither the raw nor processed record is changed because the transaction rolls back

## Processed-write rollback verification

Run the focused regression suite against the replica-set test fixture:

```bash
pytest tests/test_micro_affinity_groups_endpoint.py \
  tests/test_micro_affinity_group_relationship_mapper.py \
  tests/test_micro_affinity_group_use_case.py \
  tests/test_micro_affinity_groups_persistence.py
```

Expected:

- The processed-write failure test returns `500 Internal Server Error`
- No partial raw or processed records remain after the failed request

## Notes

- The feature-local processed response contract lives at
  `specs/008-add-mag-relationships/contracts/micro_affinity_group_processed.schema.json`.
- Implementation is expected to promote the finalized response contract into
  `specs/001-service-skeleton/contracts/` and regenerate the corresponding response model.
- Integration tests should run against a replica-set-capable MongoDB fixture because rollback
  verification depends on real multi-operation transactions.