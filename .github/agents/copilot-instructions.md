# Dependency Graph Service API Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-16

## Active Technologies
- Python 3.12 + FastAPI, Pydantic, Motor (MongoDB Atlas), LDAP3 (001-service-skeleton)
- MongoDB Atlas (via Motor) (001-service-skeleton)
- Python 3.12+ (project requires `>=3.12`) + FastAPI, Pydantic v2, Starlette (002-components-echo)
- MongoDB Atlas (existing), but **N/A for this feature** (002-components-echo)
- Python 3.12 + FastAPI, Pydantic v2, PyMongo (003-persist-components-payload)
- MongoDB (configured via `GRAPH_SERVICE_MONGODB_URI` and `GRAPH_SERVICE_MONGODB_DATABASE`) (003-persist-components-payload)
- Python 3.12+ + FastAPI, Pydantic v2, PyMongo (004-components-payload-schema)
- Python 3.12+ + FastAPI, Pydantic v2, pymongo, pydantic-settings, datamodel-code-generator, pytest, httpx/TestClient, testcontainers[mongodb] (006-calm-architecture-ingest, 007-add-micro-affinity-endpoint)
- MongoDB Atlas / MongoDB collection `application-architectures` keyed by `metadata.AssetID` + `metadata.version` (006-calm-architecture-ingest)
- MongoDB Atlas / MongoDB collection `micro-affinity-groups`, plus read access to `application-architectures` for cross-collection validation (007-add-micro-affinity-endpoint)
- Python 3.12+ + FastAPI, Pydantic v2, pymongo, pydantic-settings, datamodel-code-generator, pytest, httpx/TestClient, testcontainers[mongodb], Python standard-library `logging` (008-add-mag-relationships)
- MongoDB Atlas / MongoDB collections `micro-affinity-groups` (raw input), `micro-affinity-groups-processed` (transformed output), plus read access to `application-architectures` for transformation lookups (008-add-mag-relationships)
- Python 3.12+ (verified in the active venv on Python 3.14.3) + FastAPI, Pydantic v2, pymongo, ldap3, pytest, httpx/TestClien (009-v1-api-prefixing)
- MongoDB Atlas / MongoDB test replica set for persistence-backed endpoint tests (009-v1-api-prefixing)
- Python 3.12+ (verified in the active venv on Python 3.14.3) + FastAPI, Pydantic v2, pymongo, pytest, httpx/TestClient, testcontainers[mongodb], ldap3 (010-rename-collection-names)
- MongoDB Atlas in production; MongoDB replica-set container for persistence-backed integration tests (010-rename-collection-names)
- Python 3.12 (project baseline for scaffolding) + FastAPI, Pydantic, Motor (MongoDB), LDAP3 (001-service-skeleton)
- Python 3.12+ (active workspace venv previously verified on Python 3.14.3) + FastAPI, Pydantic v2, datamodel-code-generator, pymongo, pytest, httpx/TestClient, testcontainers[mongodb], ldap3 (011-snake-case-mag-api)

## Project Structure

```text
src/
tests/
```

## Commands

- Run tests: pytest
- Run API (after scaffold exists): an ASGI server pointing at the app factory in src/infrastructure/main.py

## Code Style

Python 3.12 (project baseline for scaffolding): Follow standard conventions

## Recent Changes
- 011-snake-case-mag-api: Added Python 3.12+ (active workspace venv previously verified on Python 3.14.3) + FastAPI, Pydantic v2, datamodel-code-generator, pymongo, pytest, httpx/TestClient, testcontainers[mongodb], ldap3
- 010-rename-collection-names: Added Python 3.12+ (verified in the active venv on Python 3.14.3) + FastAPI, Pydantic v2, pymongo, pytest, httpx/TestClient, testcontainers[mongodb], ldap3
- 009-v1-api-prefixing: Added Python 3.12+ (verified in the active venv on Python 3.14.3) + FastAPI, Pydantic v2, pymongo, ldap3, pytest, httpx/TestClien


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
