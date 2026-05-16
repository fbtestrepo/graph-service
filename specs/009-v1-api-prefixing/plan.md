# Implementation Plan: V1 API Version Prefixing

**Branch**: `009-v1-api-prefixing` | **Date**: 2026-05-16 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/009-v1-api-prefixing/spec.md`
**Input**: Feature specification from `/specs/009-v1-api-prefixing/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Move every in-scope business endpoint behind `/v1` without changing request models, response
models, dependency injection, or status-code behavior. The preferred implementation is to keep
all existing router modules unchanged and assemble them under one FastAPI-managed versioned router
at application bootstrap, while health and automatic documentation remain mounted at the root.
The implementation will update TestClient path expectations across the affected pytest suites,
add explicit checks that `/health`, `/docs`, `/redoc`, and `/openapi.json` stay unversioned, and
re-run the functional regression suite after the route migration.

## Technical Context

**Language/Version**: Python 3.12+ (verified in the active venv on Python 3.14.3)  
**Primary Dependencies**: FastAPI, Pydantic v2, pymongo, ldap3, pytest, httpx/TestClient  
**Storage**: MongoDB Atlas / MongoDB test replica set for persistence-backed endpoint tests  
**Testing**: pytest with FastAPI `TestClient`; functional regression command verified as `python -m pytest tests -v -k "not perf_smoke"`  
**Target Platform**: ASGI web service running locally on macOS/Linux and deployable to Linux server environments
**Project Type**: web-service  
**Performance Goals**: No material runtime regression; route versioning should be a registration-only change with unchanged handler behavior and no additional request-processing steps  
**Constraints**: Use FastAPI native routing composition to apply `/v1` globally; keep `GET /health`, `/docs`, `/redoc`, and `/openapi.json` at root; preserve existing Pydantic contracts, `Depends(...)` wiring, and HTTP status codes; keep folder structure unchanged; run the full functional suite excluding only non-functional perf smoke tests  
**Scale/Scope**: One application bootstrap change, zero route-function signature rewrites, one route-contract update set under `specs/009-v1-api-prefixing/`, and route-path updates across the affected endpoint and persistence test files plus new health/docs coverage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Required gates for this project (see `.specify/memory/constitution.md`):

- Architecture: Feature design preserves Hexagonal Architecture (Ports & Adapters).
- Core purity: `src/core/` remains framework-agnostic (no `fastapi`, `pymongo`/`motor`, `ldap3`, etc.).
- Ports: Any new external capability is introduced as an ABC in `src/core/ports/`.
- Specs-first: Any change to feature intent, behavioral requirements, or software specifications
  starts in `specs/`.
- Canonical contracts: Any change to shared or canonical data contracts starts in `schemas/`.
- Validation: Inbound adapter validates all JSON payloads via Pydantic schemas in
  `src/adapters/inbound/api/schemas/` before calling core use cases.
- Errors: New domain exceptions are defined in `src/core/exceptions/` and mapped to HTTP in
  `src/infrastructure/errors/` without leaking stack traces.
- Structure: Folder structure remains unchanged unless explicitly approved.

Gate assessment before Phase 0 research:

- Architecture: PASS. Versioning is isolated to FastAPI route registration in the infrastructure/
  inbound boundary and does not move business rules into adapters.
- Core purity: PASS. No changes are required in `src/core/`.
- Ports: PASS. No new external capability is introduced.
- Specs-first: PASS. The feature specification was completed under
  `specs/009-v1-api-prefixing/` before design.
- Canonical contracts: PASS. This is a service-local HTTP route change, so contract artifacts stay
  under `specs/` and do not require root `schemas/` changes.
- Validation: PASS. Existing Pydantic request validation remains unchanged because route handlers
  and schemas are preserved.
- Errors: PASS. Existing domain-error to HTTP mappings remain intact because handlers are reused.
- Structure: PASS. The feature fits the existing folders and requires no structural changes.

## Project Structure

### Documentation (this feature)

```text
specs/009-v1-api-prefixing/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── http-api.md
│   └── openapi.yaml
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
specs/
├── 009-v1-api-prefixing/
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   └── contracts/
│       ├── http-api.md
│       └── openapi.yaml

src/
├── adapters/
│   └── inbound/
│       └── api/
│           └── routers/
│               ├── application_architectures.py
│               ├── component_validation.py
│               ├── components.py
│               ├── health.py
│               └── micro_affinity_groups.py
├── infrastructure/
│   └── main.py

tests/
├── conftest.py
├── test_application_architectures_endpoint.py
├── test_application_architectures_persistence.py
├── test_component_dependencies_endpoint.py
├── test_component_dependencies_persistence.py
├── test_components_endpoint.py
├── test_components_persistence.py
├── test_components_persistence_failure.py
├── test_micro_affinity_groups_endpoint.py
├── test_micro_affinity_groups_persistence.py
├── test_validation_endpoint.py
└── test_perf_smoke_*.py
```

**Structure Decision**: Keep all existing business routers in place and assemble them under a
single version boundary in `src/infrastructure/main.py`, rather than editing every router module.
The implementation path is to create a versioned parent `APIRouter(prefix="/v1")` or equivalent
FastAPI router composition at bootstrap, include the business routers under it, keep
`health_router` directly on the app, and update the affected `tests/` files plus new
health/docs checks to reflect the supported `/v1` surface.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. The design keeps versioning inside FastAPI assembly and leaves route
  handlers, use cases, and repositories unchanged.
- Core purity: PASS. No framework or driver code crosses into `src/core/`.
- Ports: PASS. No new ports or external capabilities are needed.
- Specs-first: PASS. Research, data model, contracts, and quickstart are now captured under
  `specs/009-v1-api-prefixing/` before implementation.
- Canonical contracts: PASS. No root `schemas/` update is required because request and response
  bodies are unchanged.
- Validation: PASS. All payload validation continues through the existing inbound Pydantic models.
- Errors: PASS. Existing exception handlers and status mappings remain the source of truth.
- Structure: PASS. No new folders are introduced; only existing files and feature-spec artifacts
  are involved.
