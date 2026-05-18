# Implementation Plan: Component Dependencies Graph

**Branch**: `005-component-dependencies` | **Date**: 2026-03-26 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/005-component-dependencies/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add a new endpoint `GET /components/{node_id}/dependencies` that returns a component’s full
transitive dependency graph (upstream + downstream) as an edge list.

Edges are derived from stored component-node relationship data (as persisted by `POST /components`).
The endpoint returns `404 Not Found` when the root `node-id` does not exist, and returns
`422 Unprocessable Entity` when the root exists but downstream traversal cannot resolve required
intermediate records consistently.

Graph traversal must:
- expand one hop at a time (level-order)
- include transitive dependencies
- detect and stop cycles while still returning cycle-closing edges
- cap traversal depth at 20 hops

The response payload uses a new schema (and generated Pydantic model) matching the example in
`specs/sample-component-dependencies/sample-mag-dependencies.json`.

## Technical Context


**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, PyMongo  
**Storage**: MongoDB (configured via `GRAPH_SERVICE_MONGODB_URI` and `GRAPH_SERVICE_MONGODB_DATABASE`)  
**Testing**: pytest (unit tests + Mongo integration tests via testcontainers/Docker)  
**Target Platform**: Server (development on macOS; deploy target not specified)
**Project Type**: Web service (HTTP JSON API)  
**Performance Goals**: For reachable graphs with ~100 unique edges, keep responses fast enough to satisfy SC-003 (95/100 requests within 1s in a local run)  
**Constraints**: Hexagonal boundaries; specs-first contracts; inbound validation before core; no core framework/driver imports; Problem Details for errors; folder structure immutable  
**Scale/Scope**: Add one new GET endpoint + supporting schema/model + core traversal use case + repository queries for upstream/downstream edges

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Required gates for this project (see `.specify/memory/constitution.md`):

- Architecture: Feature design preserves Hexagonal Architecture (Ports & Adapters).
- Core purity: `src/core/` remains framework-agnostic (no `fastapi`, `pymongo`/`motor`, `ldap3`, etc.).
- Ports: Any new external capability is introduced as an ABC in `src/core/ports/`.
- Specs-first: Any API contract change starts in `specs/` (OpenAPI + JSON Schemas).
- Validation: Inbound adapter validates all JSON payloads via Pydantic schemas in
  `src/adapters/inbound/api/schemas/` before calling core use cases.
- Errors: New domain exceptions are defined in `src/core/exceptions/` and mapped to HTTP in
  `src/infrastructure/errors/` without leaking stack traces.
- Structure: Folder structure remains unchanged unless explicitly approved.

**Gate Evaluation (pre-research)**: PASS (no violations)

Notes:
- The traversal algorithm belongs in core use cases/domain helpers.
- MongoDB query capability for upstream edges must be introduced as a core port method and implemented in the Mongo adapter.

**Gate Evaluation (post-design)**: PASS (no violations)

## Project Structure

### Documentation (this feature)

```text
specs/005-component-dependencies/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Authoritative baseline structure (DO NOT change folders without explicit approval)

specs/

src/
├── core/
│   ├── domain/
│   ├── ports/
│   ├── use_cases/
│   └── exceptions/
├── adapters/
│   ├── inbound/
│   │   └── api/
│   │       ├── dependencies/
│   │       ├── routers/
│   │       └── schemas/
│   └── outbound/
│       ├── mongodb/
│       └── ldap/
└── infrastructure/
  ├── config/
  ├── errors/
  ├── middleware/
  └── main.py

tests/
```

**Structure Decision**: Implement as a contracts-first + ports-and-adapters change:
- Add a new response schema + OpenAPI path under `specs/`.
- Generate a Pydantic model for the response in `src/adapters/inbound/api/schemas/`.
- Add a core use case to compute the transitive edge list (level-order traversal with depth cap and cycle handling).
- Add/extend a core port to support reverse edge lookup (upstream traversal) via an outbound MongoDB adapter.
- Add a new FastAPI route handler that validates path params, calls the core use case, and returns the response model.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations requiring justification.

## Phase Outputs (Design Artifacts)

- Phase 0 (Research): `research.md`
- Phase 1 (Design): `data-model.md`, `contracts/`, `quickstart.md`

## Implementation Outline

1. Contracts-first updates (working copy in this feature; promote to authoritative in tasks/implementation):
  - Define a new JSON Schema for the dependency graph response.
  - Update OpenAPI working copy to add `GET /components/{node_id}/dependencies`.
2. Inbound response model:
  - Generate a Pydantic v2 model for the dependency graph response from JSON Schema.
3. Core traversal:
  - Define a domain-friendly representation of edges and a traversal algorithm that expands one hop at a time.
  - Enforce a maximum traversal depth of 20 hops.
  - Prevent infinite loops while still including cycle-closing edges.
  - Deduplicate edges and return them in deterministic order.
4. Port + adapter support for upstream traversal:
  - Extend the component-node repository port with an operation to find relationship edges incident to a set of node-ids (including reverse lookup by target).
  - Implement this query in the Mongo adapter.
5. HTTP behavior:
  - Return `404` if the root node is not found.
  - Return `422` if the root exists but downstream graph resolution fails after traversal starts.
  - Return `200` and the edge list otherwise.
6. Tests:
  - Add unit tests for traversal behavior (transitive, upstream+downstream, cycles, depth cap).
  - Add integration tests using MongoDB testcontainer to validate query correctness.
