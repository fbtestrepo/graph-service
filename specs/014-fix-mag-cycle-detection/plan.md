# Implementation Plan: Fix MAG Cycle Detection

**Branch**: `014-fix-mag-cycle-detection` | **Date**: 2026-05-19 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/014-fix-mag-cycle-detection/spec.md`
**Input**: Feature specification from `/specs/014-fix-mag-cycle-detection/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Correct the deployment-scope cycle-handling defect for cyclic graphs rooted at a requested MAG by
replacing the current global SCC-based cycle-edge selection with path-scoped back-edge detection
that respects the existing one-hop-upstream boundary before downstream traversal. The change keeps
the request/response contract intact, preserves acyclic behavior, limits implementation to the
existing deployment-scope core modules, and adds regression coverage for the reported graph plus
full-suite validation.

## Technical Context

**Language/Version**: Python 3.12+ (repo runtime; current workspace venv is Python 3.14.3)  
**Primary Dependencies**: FastAPI, Pydantic v2, pymongo, pytest, FastAPI TestClient/httpx  
**Storage**: MongoDB Atlas / `micro_affinity_groups_processed` collection  
**Testing**: pytest unit + endpoint + persistence suites, `python check_core_purity.py`, full `python -m pytest tests -v` regression run  
**Target Platform**: ASGI web service for macOS/Linux development and Linux deployment  
**Project Type**: web-service  
**Performance Goals**: Preserve existing bounded 30-hop traversal behavior, avoid whole-collection loading, and preserve current acyclic response behavior without added regressions  
**Constraints**: No request/response schema changes for the endpoint; no behavior changes for acyclic graphs; keep the fix modular inside existing core graph logic; run the full test suite with no regressions  
**Scale/Scope**: One defect fix in the deployment-scope graph algorithm, one behavior-only contract note, and targeted regression additions across use-case, endpoint, and persistence coverage

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

- Architecture: PASS. The change is isolated to the existing deployment-scope use case and pure
  core graph helper modules.
- Core purity: PASS. Cycle detection and deployment-stage calculation remain framework-agnostic in
  `src/core/`.
- Ports: PASS. No new external capability is introduced; existing repository ports remain
  sufficient.
- Specs-first: PASS. The defect behavior, expected corrected response, and scope are captured in
  `specs/014-fix-mag-cycle-detection/spec.md` before implementation.
- Canonical contracts: PASS. No root-level `schemas/` changes are required because the request and
  response shapes remain unchanged.
- Validation: PASS. Inbound validation continues to live in the existing Pydantic schemas; this is
  a pure behavior fix behind the same endpoint contract.
- Errors: PASS. The fix does not change existing domain exception families or their HTTP mapping.
- Traversal semantics: PASS. `404` versus `422` behavior is preserved unchanged.
- Structure: PASS. The plan stays within the existing repository structure.

## Project Structure

### Documentation (this feature)

```text
specs/014-fix-mag-cycle-detection/
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
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── routers/
│   │       └── schemas/
│   └── outbound/
│       └── mongodb/
├── core/
│   ├── domain/
│   │   └── micro_affinity_group_deployment_graph.py
│   ├── ports/
│   │   └── micro_affinity_group_processed_repository.py
│   ├── use_cases/
│   │   └── get_micro_affinity_group_deployment_scope.py
│   └── exceptions/
└── infrastructure/
    ├── errors/
    └── main.py

tests/
├── test_micro_affinity_group_deployment_scope_use_case.py
├── test_micro_affinity_group_deployment_scope_endpoint.py
└── test_micro_affinity_group_deployment_scope_persistence.py
```

**Structure Decision**: Keep the fix inside the existing deployment-scope use case and pure-core
graph helper so the cycle-selection rule remains testable and modular. No new folders, adapters,
or schemas are needed; only the existing deployment-scope path, persistence read path, and
regression tests are in scope.

## Phase Plan

### Phase 0 - Research And Defect Framing

- Verify the current deployment-scope implementation path and confirm where the incorrect cyclic
  edge is selected.
- Compare the current global SCC-based cycle reduction with the required path-scoped back-edge
  definition from the feature spec.
- Confirm whether any request/response contract files need modification or whether the fix is
  behavior-only behind the existing endpoint contract.

### Phase 1 - Design And Contracts

- Model the root-scoped traversal path, path-scoped cyclic edge, reduced deployment graph, and
  deployment stage as explicit planning entities.
- Document the behavioral contract delta for the deployment-scope endpoint without changing the
  existing request/response schema shape.
- Prepare a quickstart focused on reproducing the reported graph, running the targeted regression
  tests, and validating the full suite.

### Phase 2 - Implementation Planning

- Adjust the deployment-scope core graph helper to derive cyclic edges from traversal-path context
  instead of a global SCC candidate set.
- Preserve the existing one-hop-upstream boundary and downstream traversal rules while ensuring the
  reported graph marks `E1 -> C` as cyclic and leaves `C -> D` intact.
- Recalculate deployment stages from the graph reduced by only the true path-scoped cyclic edges.
- Add regression tests at the use-case, endpoint, and persistence levels for the reported graph.
- Run the full test suite to confirm no regressions, especially for acyclic graphs.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. The fix remains confined to the current deployment-scope use case and pure
  graph helper modules.
- Core purity: PASS. All behavior changes remain in framework-agnostic core code.
- Ports: PASS. Existing repository capabilities are sufficient; no new outbound integration is
  required.
- Specs-first: PASS. The defect behavior, research, data model, quickstart, and contract note are
  captured under `specs/014-fix-mag-cycle-detection/` before implementation.
- Canonical contracts: PASS. No root-level schema changes are introduced.
- Validation: PASS. The request and response validation surfaces remain unchanged.
- Errors: PASS. Existing error families and mappings are preserved.
- Traversal semantics: PASS. The endpoint continues to reserve `404` for missing root resources
  and `422` for downstream graph-resolution failures.
- Structure: PASS. No folder changes are required.
