# Quickstart: V1 API Version Prefixing

**Branch**: 009-v1-api-prefixing  
**Date**: 2026-05-16

This quickstart verifies that business endpoints move under `/v1`, infrastructure routes remain at
the root path, and the functional regression suite still passes.

## Prerequisites

- Python 3.12+
- The project virtual environment at `.venv/`
- Docker available for the MongoDB-backed persistence tests used by the functional suite

## Run the service

```bash
cd /Users/ertant/work/vscode-projects/graph-service
uvicorn src.infrastructure.main:create_app --factory --reload --port 8000
```

## Verify unversioned infrastructure routes

```bash
curl -i http://localhost:8000/health
curl -i http://localhost:8000/openapi.json
curl -i http://localhost:8000/docs
curl -i http://localhost:8000/redoc
```

Expected:

- `GET /health` returns `200 OK`
- `/openapi.json`, `/docs`, and `/redoc` remain reachable from the root path

## Verify the published OpenAPI paths are versioned

```bash
curl -s http://localhost:8000/openapi.json | grep '"/v1/components"'
curl -s http://localhost:8000/openapi.json | grep '"/v1/application-architectures"'
curl -s http://localhost:8000/openapi.json | grep '"/v1/micro-affinity-groups"'
```

Expected:

- The OpenAPI document lists business routes with `/v1/...` paths
- The OpenAPI document does not describe the former root business paths as supported routes

## Verify business requests use the `/v1` prefix

```bash
curl -i \
	-X POST http://localhost:8000/v1/components/validate \
	-H 'content-type: application/json' \
	-d '{"component_id":"comp-1","name":"Component"}'

curl -i \
	-X POST http://localhost:8000/components/validate \
	-H 'content-type: application/json' \
	-d '{"component_id":"comp-1","name":"Component"}'
```

Expected:

- `POST /v1/components/validate` returns `204 No Content`
- `POST /components/validate` returns `404 Not Found` with an `application/problem+json` response

## Run the functional regression suite

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v -k "not perf_smoke"
```

Expected:

- All functional tests pass after the route migration
- Endpoint and persistence tests target `/v1/...` for in-scope business routes
- Root health and documentation checks pass

## Optional: run the full suite including perf smoke

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v
```

Expected:

- All tests pass if the environment is configured to run the perf smoke modules

## Verified implementation regression

The functional regression command above was run after implementing the route migration and
completed successfully with:

- `81 passed`
- `3 deselected` (`perf_smoke`)

This confirms the `/v1` business-route migration and root infrastructure exclusions are working in
the active workspace.