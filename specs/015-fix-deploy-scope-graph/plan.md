# Implementation Plan: Deploy-Scope Graph Resolution Fix

**Branch**: `015-fix-deploy-scope-graph` | **Date**: 2026-06-20 | **Spec**: `/Users/ertant/work/vscode-projects/graph-service/specs/015-fix-deploy-scope-graph/spec.md`
**Input**: Feature specification from `/specs/015-fix-deploy-scope-graph/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Correct deploy-scope graph resolution so traversal starts from exactly one-hop upstream dependents
of the requested MAG (or the root when none exist), then walks downstream to build a complete
graph. Tighten cycle detection to path-scoped back-edges only, mark those edges as `is_cyclic`,
move them into `deployment_sequence.bypassed_edges`, and exclude only those edges from
deployment-step topological layering. Preserve the existing endpoint contract, error semantics,
and acyclic behavior while adding deterministic ordering guarantees and full regression coverage.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, pymongo, pytest, httpx/TestClient  
**Storage**: MongoDB Atlas / `micro_affinity_groups_processed` collection  
**Testing**: pytest (`tests/test_micro_affinity_group_deployment_scope_use_case.py`, `tests/test_micro_affinity_group_deployment_scope_endpoint.py`, `tests/test_micro_affinity_group_deployment_scope_persistence.py`) plus full suite `python -m pytest tests -v` and architecture guard `python check_core_purity.py`  
**Target Platform**: ASGI web service (Linux deploy target; local macOS development)  
**Project Type**: web-service  
**Performance Goals**: Preserve current bounded traversal behavior and avoid increased query fan-out or algorithmic regressions; maintain deterministic output ordering across repeated requests  
**Constraints**: Keep endpoint contract unchanged (`/v1/micro-affinity-groups/{id}/deployment-scope`), preserve `404` vs `422` semantics, keep topological layering logic modular and free of hardcoded scenario-specific constants  
**Scale/Scope**: Behavior-only correction in existing core traversal/cycle modules with targeted and full-suite regression verification

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

- Architecture: PASS. Changes are confined to existing core traversal/use-case modules and current
  inbound/outbound paths.
- Core purity: PASS. Traversal and cycle logic remain in `src/core/` with no framework/driver
  imports.
- Ports: PASS. Existing repository ports already support required graph reads; no new external
  capability is introduced.
- Specs-first: PASS. Feature behavior and clarifications are captured in
  `specs/015-fix-deploy-scope-graph/spec.md` before implementation.
- Canonical contracts: PASS. No root-level `schemas/` changes are required for this behavior-only
  fix.
- Validation: PASS. No request payload or inbound validation flow changes are introduced.
- Errors: PASS. Existing domain-exception mapping model is retained.
- Traversal semantics: PASS. `404` for missing root and `422` for downstream resolution failures
  are explicitly preserved.
- Structure: PASS. No folder-level changes are planned.

## Project Structure

### Documentation (this feature)

```text
specs/015-fix-deploy-scope-graph/
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
│   │   └── micro_affinity_group_deployment_graph.py
│   ├── use_cases/
│   │   └── get_micro_affinity_group_deployment_scope.py
│   ├── ports/
│   │   └── micro_affinity_group_processed_repository.py
│   └── exceptions/
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── routers/
│   │       │   └── micro_affinity_groups.py
│   │       └── schemas/
│   │           ├── micro_affinity_group_deployment_scope.py
│   │           ├── micro_affinity_group_deployment_sequence.py
│   │           ├── micro_affinity_group_deployment_edge.py
│   │           └── micro_affinity_group_deployment_step.py
│   └── outbound/
│       └── mongodb/
│           └── micro_affinity_group_processed_repository.py
└── infrastructure/
    ├── errors/
    └── main.py

tests/
├── test_micro_affinity_group_deployment_scope_use_case.py
├── test_micro_affinity_group_deployment_scope_endpoint.py
└── test_micro_affinity_group_deployment_scope_persistence.py
```

**Structure Decision**: Keep implementation scoped to the existing deploy-scope traversal path in
core (`src/core/domain/` and `src/core/use_cases/`) plus existing router/repository and regression
test files. No new adapters, schemas, or folders are required.

## Phase Plan

### Phase 0 - Research And Algorithm Decisions

- Define precise traversal start-set semantics for one-hop upstream seeding and fallback to root
  when no upstream dependents are present.
- Define path-scoped cycle detection with explicit branch-local visited initialization (root +
  immediate upstream dependents).
- Define deterministic ordering semantics that preserve sample behavior: non-cyclic edges first,
  cyclic edges last, both lexicographically sorted.
- Confirm no contract-shape or canonical-schema changes are required.

### Phase 1 - Design And Contract Delta

- Model traversal, edge classification, bypassed-edge propagation, reduced graph, and deployment
  steps as explicit planning entities.
- Document behavior-only HTTP contract delta (same endpoint and response schema; corrected graph
  and cycle behavior).
- Produce quickstart with targeted deploy-scope tests, core purity check, and full suite command
  for no-regression verification.

### Phase 2 - Implementation Planning

- Update core graph traversal implementation to seed from one-hop upstream dependents and include
  downstream closure per spec.
- Update cycle detection to mark only back-edges to nodes already present on current traversal
  path.
- Ensure cyclic edges are flagged in `dependency_graph`, duplicated in `bypassed_edges`, and
  excluded from step topological calculation.
- Preserve existing topological-layering logic and error semantics.
- Add/adjust regression tests for root `C` and root `E3` sample cases and run full test suite.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

Post-design Constitution Check re-evaluation:

- Architecture: PASS. Design keeps business rules in core and preserves adapter boundaries.
- Core purity: PASS. Planned graph logic remains framework-agnostic.
- Ports: PASS. Existing ports remain sufficient; no new external capability introduced.
- Specs-first: PASS. Plan artifacts are produced under `specs/015-fix-deploy-scope-graph/`.
- Canonical contracts: PASS. No root-level `schemas/` updates needed.
- Validation: PASS. Inbound validation responsibilities remain unchanged.
- Errors: PASS. Domain-error mapping remains unchanged and compliant.
- Traversal semantics: PASS. `404`/`422` rule is explicit in requirements and preserved in plan.
- Structure: PASS. No folder structure changes are introduced.
