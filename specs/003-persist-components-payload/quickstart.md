# Quickstart: Persist Components Payload

**Branch**: 003-persist-components-payload  
**Date**: 2026-03-21

This quickstart verifies that `POST /components` still echoes the request JSON, and now also persists it to MongoDB.

## Prerequisites

- Python 3.12+
- Docker (recommended for running MongoDB locally via a container)

## Run MongoDB locally

Option A (recommended): run MongoDB via Docker

```bash
docker run --rm -p 27017:27017 --name graph-service-mongo mongo:7
```

Option B: run a locally installed `mongod` (ensure it listens on `localhost:27017`).

## Run the service

```bash
cd /Users/ertant/work/vscode-projects/graph-service
uvicorn src.infrastructure.main:create_app --factory --reload --port 8000
```

## Verify echo + persistence

### Send a request

```bash
curl -sS -X POST http://localhost:8000/components \
  -H 'content-type: application/json' \
  -d '{"hello": "world", "n": 123}'
```

Expected:
- `200 OK`
- response body equals the submitted JSON

### Verify it was persisted

Using `mongosh`:

```bash
mongosh "mongodb://localhost:27017/graph_service" \
  --eval 'db.component_payload_records.find().sort({_id:-1}).limit(1).pretty()'
```

Expected:
- a document containing `received_at` and `payload` matching the submitted JSON

## Notes

- If persistence fails, the request should return `500 application/problem+json` (no false `200`).
- This feature does not add read/list APIs for persisted records.
