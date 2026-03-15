# Quickstart: Service Architectural Skeleton

**Branch**: 001-service-skeleton  
**Date**: 2026-03-14

This quickstart is for the scaffolded service skeleton (health endpoint + wiring + guardrails).

## Prerequisites

- Python 3.12+

## Install

Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e '.[dev]'
```

## Run (development)

Environment variables (all optional; defaults exist):

- `GRAPH_SERVICE_MONGODB_URI` (default: `mongodb://localhost:27017`)
- `GRAPH_SERVICE_MONGODB_DATABASE` (default: `graph_service`)
- `GRAPH_SERVICE_LDAP_SERVER_URI` (default: `ldap://localhost:389`)
- `GRAPH_SERVICE_LDAP_BIND_DN` (default: empty)
- `GRAPH_SERVICE_LDAP_BIND_PASSWORD` (default: empty)

Run the ASGI server:

```bash
uvicorn src.infrastructure.main:create_app --factory --reload --port 8000
```

## Verify

- Call `GET /health` and expect `200` and JSON body with `status: ok`.
- Call `POST /components/validate` with a valid component body and expect `204`.
- Call `GET /components/{component_id}` and expect `200` or `404` Problem Details.

## Notes

- Error responses use RFC 7807 Problem Details (`application/problem+json`).
- Core purity is enforced via CI import-boundary checks.
- Inbound schemas are generated from `specs/` and checked for drift in CI.
