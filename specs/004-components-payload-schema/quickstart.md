# Quickstart: Components Payload Validation & Upsert

**Branch**: 004-components-payload-schema  
**Date**: 2026-03-24

This quickstart verifies that `POST /components` validates a component-node payload and upserts it in MongoDB keyed by `node-id`.

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

## Send a valid upsert request

The sample payload is located at `specs/sample-component-payload/sample-mag.json`.

### First request (expected 201)

```bash
curl -i -sS -X POST http://localhost:8000/components \
  -H 'content-type: application/json' \
  --data-binary @specs/sample-component-payload/sample-mag.json
```

Expected:
- Status: `201 Created`
- Response body equals the submitted JSON object

### Second request with the same node-id (expected 200)

```bash
curl -i -sS -X POST http://localhost:8000/components \
  -H 'content-type: application/json' \
  --data-binary @specs/sample-component-payload/sample-mag.json
```

Expected:
- Status: `200 OK`
- Response body equals the submitted JSON object

## Verify it was persisted (latest state)

Using `mongosh`:

```bash
mongosh "mongodb://localhost:27017/graph_service" \
  --eval 'db.components.find({"node-id":"mAG_A"}).pretty()'
```

Expected:
- Exactly one document with `node-id: "mAG_A"`
- The stored document reflects the latest submitted payload

## Verify it via `GET /components/{node-id}`

```bash
curl -i -sS http://localhost:8000/components/mAG_A
```

Expected:
- Status: `200 OK`
- Response body equals the stored component-node payload

Missing node-id example:

```bash
curl -i -sS http://localhost:8000/components/does-not-exist
```

Expected:
- Status: `404 Not Found`
- Response content-type: `application/problem+json`

## Notes

- Malformed JSON returns `400 application/problem+json`.
- Schema/constraint validation failures return `422 application/problem+json`.
- Persistence failures return `500 application/problem+json`.
