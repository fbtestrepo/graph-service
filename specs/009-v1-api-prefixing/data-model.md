# Data Model: V1 API Version Prefixing

**Branch**: 009-v1-api-prefixing  
**Date**: 2026-05-16

## Overview

This feature does not change business payload schemas or persistence documents. Its design model is
the published HTTP route surface: which route families move under `/v1`, which ones remain at the
root, and how the automated test suites assert that boundary.

## Entity: BusinessRouteFamily

Represents one current business-facing route group that will be published under `/v1`.

### Fields

- **`name`** (string, required): Logical route family name, for example `components` or
  `micro-affinity-groups`.
- **`current-base-path`** (string, required): The currently registered root path before the
  migration.
- **`versioned-base-path`** (string, required): The supported path after the migration, always
  prefixed with `/v1`.
- **`operations`** (array, required): The HTTP operations exposed by the route family.
- **`preserved-contracts`** (array, required): Request and response semantics that must remain
  unchanged, including payload shape, path parameter meaning, dependency wiring, and status codes.

### Route Families in Scope

- **Components Validation**
  - `current-base-path`: `/components/validate`
  - `versioned-base-path`: `/v1/components/validate`
  - `operations`: `POST`
- **Components**
  - `current-base-path`: `/components`
  - `versioned-base-path`: `/v1/components`
  - `operations`: `POST`, `GET /{component_id}`, `GET /{node_id}/dependencies`
- **Application Architectures**
  - `current-base-path`: `/application-architectures`
  - `versioned-base-path`: `/v1/application-architectures`
  - `operations`: `POST`
- **Micro Affinity Groups**
  - `current-base-path`: `/micro-affinity-groups`
  - `versioned-base-path`: `/v1/micro-affinity-groups`
  - `operations`: `POST`

### Validation Rules

- Each business route family must be registered exactly once as a supported public route surface.
- After migration, the supported public address for each in-scope business route family is its
  `/v1` path.
- Route handlers, payload models, dependency providers, and status code behavior remain unchanged.

## Entity: RootInfrastructureRoute

Represents an operational or documentation route that must remain outside the version boundary.

### Fields

- **`path`** (string, required): Published root path.
- **`category`** (string, required): `health` or `documentation`.
- **`must-remain-root`** (boolean, required): Always `true` for this feature.

### Routes in Scope

- `/health`
- `/docs`
- `/redoc`
- `/openapi.json`

### Validation Rules

- These routes remain reachable at the root path after business-route versioning is introduced.
- These routes are not re-published under `/v1` for this feature.

## Entity: RouteRegistrationBoundary

Represents the application-layer composition that attaches routers to the FastAPI app.

### Fields

- **`version-prefix`** (string, required): `/v1`
- **`business-router-set`** (array, required): The routers mounted under the version boundary.
- **`root-router-set`** (array, required): Routers or app-level endpoints mounted without the
  version prefix.

### Rules

- The version prefix is applied in the app bootstrap, not inside individual business router logic.
- Health remains outside the versioned router set.
- FastAPI app-level documentation URLs remain outside the versioned router set.

## Entity: RouteRegressionSuite

Represents the pytest suites that assert the public route contract.

### Fields

- **`file`** (string, required): Test file path.
- **`route-family`** (string, required): The business or infrastructure route family covered.
- **`assertion-type`** (string, required): Endpoint success/error, persistence, documentation
  availability, or unsupported legacy route behavior.

### Affected Suites

- `tests/test_validation_endpoint.py`
- `tests/test_components_endpoint.py`
- `tests/test_components_persistence.py`
- `tests/test_components_persistence_failure.py`
- `tests/test_component_dependencies_endpoint.py`
- `tests/test_component_dependencies_persistence.py`
- `tests/test_application_architectures_endpoint.py`
- `tests/test_application_architectures_persistence.py`
- `tests/test_micro_affinity_groups_endpoint.py`
- `tests/test_micro_affinity_groups_persistence.py`
- `tests/test_perf_smoke_*.py` for optional path alignment after the functional gate

### Validation Rules

- Functional regression must pass with business requests sent to `/v1/...` paths.
- Health and docs coverage must assert root-path availability.
- At least one test must verify that former root business paths are no longer the supported public
  addresses.

## Lifecycle / State Transitions

- **Current State**: Business routes are reachable only from root paths.
- **Migrated State**: In-scope business routes are reachable from `/v1/...`; infrastructure routes
  remain at root.
- **Unsupported Legacy State**: Former root business paths are not kept as the supported contract
  after migration.