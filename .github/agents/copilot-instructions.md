# Dependency Graph Service API Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-02

## Active Technologies
- Python 3.12 + FastAPI, Pydantic, Motor (MongoDB Atlas), LDAP3 (001-service-skeleton)
- MongoDB Atlas (via Motor) (001-service-skeleton)
- Python 3.12+ (project requires `>=3.12`) + FastAPI, Pydantic v2, Starlette (002-components-echo)
- MongoDB Atlas (existing), but **N/A for this feature** (002-components-echo)
- Python 3.12 + FastAPI, Pydantic v2, PyMongo (003-persist-components-payload)
- MongoDB (configured via `GRAPH_SERVICE_MONGODB_URI` and `GRAPH_SERVICE_MONGODB_DATABASE`) (003-persist-components-payload)
- Python 3.12+ + FastAPI, Pydantic v2, PyMongo (004-components-payload-schema)
- Python 3.12+ + FastAPI, Pydantic v2, pymongo, pydantic-settings, datamodel-code-generator, pytest, httpx/TestClient, testcontainers[mongodb] (006-calm-architecture-ingest)
- MongoDB Atlas / MongoDB collection `application-architectures` keyed by `metadata.AssetID` + `metadata.version` (006-calm-architecture-ingest)

- Python 3.12 (project baseline for scaffolding) + FastAPI, Pydantic, Motor (MongoDB), LDAP3 (001-service-skeleton)

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
- 006-calm-architecture-ingest: Added Python 3.12+ + FastAPI, Pydantic v2, pymongo, pydantic-settings, datamodel-code-generator, pytest, httpx/TestClient, testcontainers[mongodb]
- 005-component-dependencies: Added Python 3.12+ + FastAPI, Pydantic v2, PyMongo
- 004-components-payload-schema: Added Python 3.12+ + FastAPI, Pydantic v2, PyMongo


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
