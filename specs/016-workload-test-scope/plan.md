# Implementation Plan: Workload Test Scope Endpoint

**Branch**: `016-workload-test-scope` | **Date**: 2026-06-23 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/016-workload-test-scope/spec.md`
**Input**: Feature specification from `/specs/016-workload-test-scope/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add a new endpoint, `POST /v1/micro-affinity-groups/workloads/test-scope`, that computes
environment-scoped test impact for changed workload asset IDs. The design resolves affected
workload relationships from both source and destination perspectives, joins each endpoint workload
to its owning micro affinity group by workload asset ownership in the same environment, excludes
unresolved relationships, reports unknown workloads, and returns deterministic snake_case output
with summary counters. Query execution remains optimized through environment-filtered MongoDB
query/aggregation paths and avoids full-collection materialization.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, pymongo, pytest, httpx/TestClient  
**Storage**: MongoDB Atlas (`micro_affinity_groups_processed` collection)  
**Testing**: pytest endpoint/use-case/persistence suites plus full suite (`python -m pytest tests -v`) and purity guard (`python check_core_purity.py`)  
**Target Platform**: ASGI web service (Linux deployment target; macOS local development)
**Project Type**: web-service  
**Performance Goals**: Keep request processing environment-scoped and avoid full collection reads by using targeted query/aggregation patterns; maintain deterministic output ordering; in local smoke tests with representative fixture data, p95 endpoint latency SHOULD remain <= 300 ms and p99 <= 600 ms.  
**Constraints**: Preserve hexagonal boundaries; maintain snake_case response contract; return `422` for missing/blank environment validation; return `200` no-data payload when environment has no records  
**Scale/Scope**: One new POST endpoint, one new use case, port/repository query expansion, new inbound Pydantic schemas, and comprehensive regression coverage

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
- Traversal semantics: For graph-traversal or graph-resolution endpoints, `404` is reserved for a
  missing primary path resource; once that resource exists, downstream graph-resolution failures
  map to `422`.
- Structure: Folder structure remains unchanged unless explicitly approved.

Gate assessment before Phase 0 research:

- Architecture: PASS. Business rules are planned in core use-case/domain code; adapters remain thin.
- Core purity: PASS. No framework/driver imports are planned in `src/core/`.
- Ports: PASS. Mongo query capability is added through the existing processed-repository port.
- Specs-first: PASS. Feature behavior is already defined in `specs/016-workload-test-scope/spec.md`.
- Canonical contracts: PASS. No root-level `schemas/` changes are required for this endpoint.
- Validation: PASS. Inbound Pydantic schemas will validate request/response before/after core use case.
- Errors: PASS. Domain and validation errors remain mapped via `src/infrastructure/errors/`.
- Traversal semantics: PASS. Validation and downstream resolution semantics keep `422` where required.
- Structure: PASS. No folder-level changes are required.

## Project Structure

### Documentation (this feature)

```text
specs/016-workload-test-scope/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── http-api.md
└── tasks.md
```

### Source Code (repository root)
```text
src/
├── core/
│   ├── domain/
│   ├── ports/
│   │   └── micro_affinity_group_processed_repository.py
│   ├── use_cases/
│   │   └── get_workload_test_scope.py
│   └── exceptions/
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── routers/
│   │       │   └── micro_affinity_groups.py
│   │       └── schemas/
│   │           └── workload_test_scope.py
│   └── outbound/
│       └── mongodb/
│           └── micro_affinity_group_processed_repository.py
└── infrastructure/
    └── errors/

tests/
├── test_workload_test_scope_endpoint.py
├── test_workload_test_scope_use_case.py
└── test_workload_test_scope_persistence.py
```

**Structure Decision**: Add the endpoint through the existing micro-affinity router and processed
repository adapter, with new request/response schemas in inbound adapter code and new business
logic in a dedicated core use case. Keep folder structure unchanged; only add files within
existing directories.

## Phase Plan

### Phase 0 - Research And Design Decisions

- Decide optimized MongoDB query/aggregation strategy for workload-to-MAG ownership matching,
  with environment filter enforced in every lookup.
- Decide unresolved relationship behavior: exclude unresolved relationships and report unresolved
  endpoint workloads in `unknown_workloads`.
- Decide deterministic ordering and deduplication strategy: first-seen order for input-driven
  arrays and lexicographic ordering for affected relationship pairs.
- Confirm request validation and error semantics (`422` for missing/blank environment) remain
  aligned with constitution and existing handler behavior.

### Phase 1 - Data Model, Contracts, And Test Design

- Define request/response entities and invariants for changed workloads, affected relationships,
  unknown workloads, and summary counters.
- Define endpoint contract for media types, statuses, request schema, response schema, and
  deterministic ordering rules.
- Define comprehensive test matrix for source traversal, destination traversal, dual-role
  workloads, environment isolation, unknown workloads, empty input, missing environment, summary
  math, and response-contract validation.

### Phase 2 - Implementation Planning

- Extend processed repository port/adapter with a targeted query/aggregation method for workload
  relationship resolution in environment scope.
- Implement core use case to build response payload with deduplication, unresolved handling,
  ordering, and summary math.
- Add inbound Pydantic models for request/response payloads and wire new POST route under
  `/v1/micro-affinity-groups/workloads/test-scope`.
- Add endpoint/use-case/persistence tests and run full regression plus core purity check.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. Data resolution logic remains in core use case; adapters perform I/O only.
- Core purity: PASS. Planned logic keeps framework/database imports out of `src/core/`.
- Ports: PASS. Repository capability is surfaced through an explicit core port method.
- Specs-first: PASS. Planning artifacts are generated under `specs/016-workload-test-scope/`.
- Canonical contracts: PASS. No canonical schema update is required for this endpoint.
- Validation: PASS. Inbound schemas cover payload validation and enforce snake_case contract shape.
- Errors: PASS. Validation/domain errors continue through existing centralized HTTP mapping.
- Traversal semantics: PASS. Missing/blank environment maps to `422` with no core processing.
- Structure: PASS. No folder add/remove/rename is planned.
