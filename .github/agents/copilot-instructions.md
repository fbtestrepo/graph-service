# Dependency Graph Service API Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-19

## Active Technologies
- Python 3.12 + FastAPI, Pydantic, Motor (MongoDB Atlas), LDAP3 (001-service-skeleton)
- MongoDB Atlas (via Motor) (001-service-skeleton)
- Python 3.12+ (project requires `>=3.12`) + FastAPI, Pydantic v2, Starlette (002-components-echo)
- MongoDB Atlas (existing), but **N/A for this feature** (002-components-echo)

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
- 002-components-echo: Added Python 3.12+ (project requires `>=3.12`) + FastAPI, Pydantic v2, Starlette
- 001-service-skeleton: Added Python 3.12 + FastAPI, Pydantic, Motor (MongoDB Atlas), LDAP3

- 001-service-skeleton: Added Python 3.12 (project baseline for scaffolding) + FastAPI, Pydantic, Motor (MongoDB), LDAP3

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
