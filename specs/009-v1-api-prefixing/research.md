# Research: V1 API Version Prefixing

**Branch**: 009-v1-api-prefixing  
**Date**: 2026-05-16

## Decisions

### Decision 1: Apply `/v1` through one versioned router assembly in the app bootstrap

- **Decision**: Compose the business routers under one FastAPI-managed version boundary in
  `src/infrastructure/main.py`, using a parent `APIRouter(prefix="/v1")` or equivalent
  `include_router(..., prefix="/v1")` registration pattern, instead of editing every router
  module's local prefix.
- **Rationale**:
  - The current router modules already describe stable business subpaths such as `/components` and
    `/micro-affinity-groups`; versioning is an application-assembly concern rather than a
    handler concern.
  - A single bootstrap change satisfies the architectural-fit requirement to leverage FastAPI's
    native routing composition instead of manually rewriting each router file.
  - This keeps future versioning extensible because a `v2` router boundary can be added without
    disturbing the existing business router modules.
- **Alternatives considered**:
  - Edit each router to embed `/v1` in its `APIRouter(prefix=...)`: rejected because it spreads
    versioning policy across multiple files and creates avoidable churn.
  - Add manual duplicate endpoints beside the root routes: rejected because the spec explicitly
    says the former root business paths should no longer remain the supported routes.

### Decision 2: Keep health and automatic documentation at the root path

- **Decision**: Continue mounting `health_router` directly on the app and leave FastAPI's
  automatic `/docs`, `/redoc`, and `/openapi.json` URLs unmodified at the root.
- **Rationale**:
  - The feature specification explicitly excludes these infrastructure and discovery routes from
    versioning.
  - FastAPI exposes docs and OpenAPI endpoints at the app level, so router prefix changes do not
    require special handling to preserve them at root.
  - Keeping them unversioned avoids breaking operational checks and documentation entry points.
- **Alternatives considered**:
  - Move docs and health under `/v1` for consistency: rejected because it contradicts the spec.
  - Duplicate docs and health at both root and `/v1`: rejected because it adds unnecessary surface
    area and weakens the contract boundary.

### Decision 3: Preserve request and response models exactly as they are

- **Decision**: Do not change any Pydantic schema, route function signature, dependency provider,
  or use-case invocation. Only the registered public path changes for the in-scope business
  routes.
- **Rationale**:
  - The specification and user constraints explicitly preserve payload semantics, dependency
    injection, and HTTP status codes.
  - Current handlers already rely on generated or existing schemas and on stable `Depends(...)`
    wiring that does not need to know about API versioning.
  - Restricting the change to routing reduces regression risk and keeps the core untouched.
- **Alternatives considered**:
  - Introduce versioned duplicates of Pydantic models: rejected because request/response bodies are
    unchanged.
  - Rewrite handlers around a new versioning abstraction: rejected because it adds complexity with
    no functional gain.

### Decision 4: Update tests by route-family inventory and add explicit unversioned-root checks

- **Decision**: Use the existing test inventory to update every hardcoded business path to its
  `/v1` equivalent in the affected TestClient suites, and add new checks that `/health`, `/docs`,
  `/redoc`, and `/openapi.json` remain reachable at root and that old root business paths are no
  longer the supported addresses.
- **Rationale**:
  - Workspace search identified hardcoded business-path usage across endpoint, persistence, and
    performance-smoke tests, concentrated in 11 files.
  - The current suite does not cover the root infrastructure routes, so explicit health/docs tests
    are needed to lock in the exclusion requirement.
  - Adding negative coverage for former root business paths makes the contract transition explicit
    and protects against accidental duplicate registration.
- **Alternatives considered**:
  - Update tests opportunistically during implementation without an inventory: rejected because it
    risks missing persistence or dependency-route coverage.
  - Skip negative old-path coverage: rejected because the spec says the root business paths should
    no longer remain supported.

### Decision 5: Use the non-perf functional regression command as the required verification gate

- **Decision**: Treat `python -m pytest tests -v -k "not perf_smoke"` as the required functional
  regression command for this feature, and record the current baseline result as 73 passed,
  3 deselected.
- **Rationale**:
  - The repo's `tests/` directory mixes endpoint/persistence/use-case tests with three perf-smoke
    modules whose purpose is non-functional validation.
  - Running the non-perf suite exercises the functional behavior relevant to this route migration
    while avoiding throughput-focused cases that are outside the requested regression scope.
  - The baseline command already completed successfully in the active environment, so it is a
    verified, not hypothetical, test gate.
- **Alternatives considered**:
  - Run only endpoint tests: rejected because persistence-backed and use-case tests also protect
    the public business routes indirectly.
  - Treat perf smoke as part of the required functional gate: rejected because those tests are
    non-functional by intent.

## Open Questions

None. All planning-time clarifications are resolved.