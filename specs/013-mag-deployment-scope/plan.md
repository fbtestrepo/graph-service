# Implementation Plan: MAG Deployment Scope

**Branch**: `013-mag-deployment-scope` | **Date**: 2026-05-17 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/013-mag-deployment-scope/spec.md`
**Input**: Feature specification from `/specs/013-mag-deployment-scope/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add a read-only endpoint at `GET /v1/micro-affinity-groups/{id}/deployment-scope` that reads
from `micro_affinity_groups_processed`, resolves one hop of inverse upstream dependents plus full
downstream MAG dependencies within the requested environment, detects and surfaces cycles, and
returns a snake_case deployment-scope document matching the sample contract. The design keeps the
HTTP layer thin, introduces a reusable core graph-building use case plus a processed-MAG read port
optimized for per-hop MongoDB queries, adds a dedicated response contract for later Pydantic
codegen, and preserves the constitution rule that missing roots are `404` while broken downstream
resolution after root discovery is `422`.

## Technical Context

**Language/Version**: Python 3.12+ (repo runtime), implemented in the existing ASGI service stack  
**Primary Dependencies**: FastAPI, Pydantic v2, pymongo, pytest, FastAPI TestClient/httpx, testcontainers[mongodb], ldap3, datamodel-code-generator  
**Storage**: MongoDB Atlas in production; read-only access to `micro_affinity_groups_processed` for this feature; MongoDB containers for persistence-backed tests  
**Testing**: pytest unit + endpoint + persistence suites, `python check_core_purity.py`, plus full regression via `python -m pytest tests -v`  
**Target Platform**: ASGI web service for macOS/Linux development and Linux server deployment
**Project Type**: web-service  
**Performance Goals**: Resolve the graph via optimized MongoDB queries or aggregation per hop without pulling the full collection into memory; keep traversal bounded to 30 hops; preserve deterministic output ordering across repeated requests against unchanged data  
**Constraints**: Preserve Hexagonal Architecture; query only `micro_affinity_groups_processed`; environment-specific joins only; one-hop inverse upstream plus downstream traversal up to the supported 30-hop boundary; read-only endpoint with no persistence side effects; deterministic cycle-breaking and ordering; define response contracts for later Pydantic model/codegen integration; run the full test suite with no regressions  
**Scale/Scope**: One new GET endpoint, one response contract family, one new core graph/deployment-scope use case plus reusable graph helpers, an extension of the processed-MAG read port and MongoDB adapter, new domain exceptions/error mappings, and MAG-specific tests plus full-suite regression

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

- Architecture: PASS. The endpoint fits the current router -> use case -> repository -> error
  mapping flow and can reuse MAG modules without introducing cross-layer leaks.
- Core purity: PASS. Graph traversal, cycle reduction, and deployment layering belong in the core
  and do not require framework or driver imports.
- Ports: PASS. The feature needs new read capabilities on the processed-MAG repository port rather
  than direct MongoDB access from the use case.
- Specs-first: PASS. Feature intent, clarified behavior, and contract decisions are already
  captured under `/Users/ertant/work/vscode-projects/graph-service/specs/013-mag-deployment-scope/`.
- Canonical contracts: PASS. The feature introduces service-local API contracts under `specs/013`;
  no root-level `schemas/` changes are required.
- Validation: PASS. The endpoint has path/query validation at the API boundary and will emit a
  dedicated response model through generated or maintained Pydantic schemas.
- Errors: PASS. The plan uses domain exceptions for missing root and downstream graph failures and
  maps them via the existing infrastructure handlers.
- Structure: PASS. The design reuses current folders only.

## Project Structure

### Documentation (this feature)

```text
specs/013-mag-deployment-scope/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── deployment_scope_response.schema.json
│   ├── deployment_sequence.schema.json
│   ├── deployment_step.schema.json
│   ├── micro_ag_edge.schema.json
│   ├── http-api.md
│   └── openapi.yaml
└── tasks.md             # Created later by /speckit.tasks
```

### Source Code (repository root)
```text
specs/
├── 001-service-skeleton/
│   └── contracts/
│       ├── problem_details.schema.json
│       └── openapi.yaml
├── 013-mag-deployment-scope/
│   ├── plan.md
│   ├── research.md
│   ├── data-model.md
│   ├── quickstart.md
│   └── contracts/
│       ├── deployment_scope_response.schema.json
│       ├── deployment_sequence.schema.json
│       ├── deployment_step.schema.json
│       ├── micro_ag_edge.schema.json
│       ├── http-api.md
│       └── openapi.yaml

schemas/

src/
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── dependencies/
│   │       ├── routers/
│   │       │   └── micro_affinity_groups.py
│   │       └── schemas/
│   │           ├── micro_affinity_group_processed.py
│   │           └── micro_affinity_group_deployment_scope.py   # generated/maintained later
│   └── outbound/
│       └── mongodb/
│           ├── collection_names.py
│           └── micro_affinity_group_processed_repository.py
├── core/
│   ├── domain/
│   │   ├── micro_affinity_group_relationship_mapper.py
│   │   ├── micro_affinity_group_deployment_graph.py
│   │   ├── dependency_edge.py
│   │   └── dependency_graph.py
│   ├── exceptions/
│   │   ├── micro_affinity_group_not_found.py
│   │   └── micro_affinity_group_graph_resolution_error.py
│   ├── ports/
│   │   └── micro_affinity_group_processed_repository.py
│   └── use_cases/
│       ├── upsert_micro_affinity_group.py
│       └── get_micro_affinity_group_deployment_scope.py
└── infrastructure/
    ├── config/
    ├── errors/
    │   ├── handlers.py
    │   └── mappers.py
    ├── middleware/
    └── main.py

tests/
├── test_micro_affinity_groups_endpoint.py
├── test_micro_affinity_groups_persistence.py
├── test_micro_affinity_group_relationship_mapper.py
├── test_micro_affinity_group_use_case.py
├── test_micro_affinity_group_deployment_scope_endpoint.py
├── test_micro_affinity_group_deployment_scope_use_case.py
└── test_micro_affinity_group_deployment_scope_persistence.py
```

**Structure Decision**: Keep the endpoint inside the existing Micro-AG router and repository
surface, add one dedicated read use case for deployment-scope generation, extend only the
processed-MAG repository port and MongoDB adapter for graph-resolution queries, and add one
feature-local response contract family under `specs/013-mag-deployment-scope/contracts/`. Graph
resolution logic stays in the core for reuse by future MAG graph endpoints, while HTTP and
MongoDB-specific details remain confined to the adapter layers.

## Phase Plan

### Phase 0 - Contract, Query, And Reuse Audit

- Confirm the endpoint is read-only and that `micro_affinity_groups_processed` is the only data
  source used for graph resolution.
- Audit current MAG router, processed repository, and error-mapping patterns to identify the exact
  files that can be extended instead of duplicated.
- Resolve the optimized query strategy for destination-workload asset matching, including
  environment scoping, self-edge suppression, and bounded 30-hop traversal.
- Decide the contract artifact set needed for later Pydantic/codegen work and document any repo
  caveat around staging schemas into `specs/001-service-skeleton/contracts/` or extending the
  generator.

### Phase 1 - Boundary And Model Design

- Define the deployment-scope response schema family under
  `/Users/ertant/work/vscode-projects/graph-service/specs/013-mag-deployment-scope/contracts/`.
- Model the response as snake_case-only output with deterministic ordering rules baked into the
  contract and sample validation.
- Keep validation and serialization concerns in the inbound adapter layer; the core returns domain
  values that map cleanly into the generated response model.
- Design failure surfaces so root lookup happens before traversal, preserving `404` for missing
  `(micro_ag_id, environment)` and `422` for downstream graph-resolution failures.

### Phase 2 - Core Graph Engine And Repository Design

- Add a reusable core use case, `get_micro_affinity_group_deployment_scope`, that orchestrates:
  - root document lookup;
  - one-hop inverse upstream expansion;
  - full downstream traversal up to 30 hops;
  - MAG-edge deduplication;
  - cycle detection and deterministic bypass selection;
  - deployment-step generation from the reduced DAG.
- Extend the processed-MAG repository port with read methods that support:
  - root lookup by `(micro_ag_id, environment)`;
  - destination-workload asset matching within an environment;
  - batched retrieval of source/destination asset ownership data needed for one-hop frontier
    expansion.
- Keep graph construction modular by separating:
  - MongoDB-backed edge discovery;
  - in-memory graph reduction and ordering;
  - response shaping.
- Map new domain exceptions in `src/infrastructure/errors/mappers.py` and
  `src/infrastructure/errors/handlers.py`.

### Phase 3 - Test And Validation Design

- Add unit coverage for linear chains, branching graphs, 30-hop truncation, cycles, and
  disconnected data.
- Add persistence-backed tests for workload-to-MAG mapping, environment-specific joins, and
  intra-group suppression.
- Add endpoint coverage for 404 guard, 422 downstream failure, snake_case compliance, and parallel
  deployment grouping.
- Validate with focused deployment-scope suites, then `python check_core_purity.py`, then the full
  project test suite to satisfy the feature request’s regression requirement.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. Core graph and deployment-order logic remain in the use case/domain layer;
  the router stays thin and the Mongo adapter owns query mechanics.
- Core purity: PASS. The design introduces no framework or driver imports into `src/core/`.
- Ports: PASS. New repository read capabilities are defined through the processed-MAG port before
  any Mongo implementation work.
- Specs-first: PASS. The feature spec, research, data model, quickstart, and contracts all live
  under `specs/013-mag-deployment-scope/` before implementation.
- Canonical contracts: PASS. No root-level `schemas/` updates are needed because the endpoint
  introduces service-local response contracts only.
- Validation: PASS. Path/query validation and response schema ownership remain in the inbound
  adapter layer.
- Errors: PASS. Missing root and downstream graph failures are explicitly planned as mapped domain
  exceptions.
- Structure: PASS. The design stays within the existing project blueprint.
