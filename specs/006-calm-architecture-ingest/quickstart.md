# Quickstart: CALM Architecture Document Ingestion

**Branch**: 006-calm-architecture-ingest  
**Date**: 2026-05-02

This quickstart verifies that `POST /application-architectures` validates a CALM document,
enforces strict root metadata rules, and upserts the payload into MongoDB keyed by
`metadata.AssetID` + `metadata.version`.

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

## Create a valid sample request body

```bash
cat > /tmp/application-architecture.json <<'JSON'
{
  "metadata": {
    "AssetID": "Asset123",
    "version": "1.0.0",
    "created": "2026-05-02"
  },
  "nodes": [],
  "relationships": []
}
JSON
```

## First request (expected 201)

```bash
curl -i -sS -X POST http://localhost:8000/application-architectures \
  -H 'content-type: application/json' \
  --data-binary @/tmp/application-architecture.json
```

Expected:

- Status: `201 Created`
- Response body equals the stored application architecture document

## Second request with the same AssetID + version (expected 200)

```bash
curl -i -sS -X POST http://localhost:8000/application-architectures \
  -H 'content-type: application/json' \
  --data-binary @/tmp/application-architecture.json
```

Expected:

- Status: `200 OK`
- Response body equals the stored application architecture document

## Verify the record in MongoDB

```bash
mongosh "mongodb://localhost:27017/graph_service" \
  --eval 'db.getCollection("application-architectures").find({"metadata.AssetID":"Asset123","metadata.version":"1.0.0"}).pretty()'
```

Expected:

- Exactly one document exists for `Asset123` version `1.0.0`
- The stored document matches the latest submitted payload

## Invalid metadata examples

### Invalid AssetID (expected 422)

```bash
cat > /tmp/application-architecture-invalid-asset.json <<'JSON'
{
  "metadata": {
    "AssetID": "Asset-123",
    "version": "1.0.0",
    "created": "2026-05-02"
  },
  "nodes": [],
  "relationships": []
}
JSON

curl -i -sS -X POST http://localhost:8000/application-architectures \
  -H 'content-type: application/json' \
  --data-binary @/tmp/application-architecture-invalid-asset.json
```

Expected:

- Status: `422 Unprocessable Entity`
- Response content-type: `application/problem+json`

### Malformed JSON (expected 400)

```bash
printf '{' | curl -i -sS -X POST http://localhost:8000/application-architectures \
  -H 'content-type: application/json' \
  --data-binary @-
```

Expected:

- Status: `400 Bad Request`
- Response content-type: `application/problem+json`

## Notes

- The authoritative service contract used for code generation lives at
  `specs/001-service-skeleton/contracts/application_architecture.schema.json` and wraps the
  canonical CALM entry schema `schemas/calm/v1_2/calm.json`.
- Validation failures for `AssetID`, `version`, `created`, or the wider CALM payload return
  `422 application/problem+json`.
- Persistence failures return `500 application/problem+json` without leaking internal details.
- Generated inbound models should be refreshed via `./generate_inbound_models.sh` after contract
  updates.