# Implementation Plan: Components Echo Endpoint

**Branch**: `002-components-echo` | **Date**: 2026-03-19 | **Spec**: `spec.md`
**Input**: Feature specification from `/Users/ertant/work/vscode-projects/graph-service/specs/002-components-echo/spec.md`

## Summary

Add `POST /components` to accept any valid JSON value, echo the same JSON back in the response,
and log the received payload once per request with truncation to the first 4096 characters (with truncation
indicated). Update API contracts (OpenAPI + JSON Schemas) and extend tests for object/array and
malformed JSON.

## Technical Context

**Language/Version**: Python 3.12+ (project requires `>=3.12`)  
**Primary Dependencies**: FastAPI, Pydantic v2, Starlette  
**Storage**: MongoDB Atlas (existing), but **N/A for this feature**  
**Testing**: pytest + FastAPI `TestClient`  
**Target Platform**: Server (local development on macOS; deploy target not specified)  
**Project Type**: Web service (HTTP JSON API)  
**Performance Goals**: Not specified (small endpoint)  
**Constraints**: Specs-first contracts; inbound validation; RFC7807 Problem Details; keep `src/core/` pure  
**Scale/Scope**: One new endpoint + contract updates + tests; no new domain logic

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
**Gate Evaluation (post-design)**: PASS (no violations)

## Project Structure

### Documentation (this feature)

```text
specs/002-components-echo/
├── spec.md              # Feature spec (source requirements)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI + JSON Schemas)
├── checklists/          # Spec checklists
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

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

**Structure Decision**: Adopt the constitution’s baseline structure exactly. Implement the new
endpoint as a new `POST` handler within the existing router module
`src/adapters/inbound/api/routers/components.py`.

## Phase Outputs (Design Artifacts)

- Phase 0 (Research): `research.md`
- Phase 1 (Design): `data-model.md`, `contracts/`, `quickstart.md`

## Implementation Outline

1. **Contracts first (authoritative)**
   - Add `POST /components` to the OpenAPI contract and introduce a JSON Schema that represents
     an “any JSON value” payload (`json_value.schema.json`).
   - Ensure error responses are documented:
     - `400 application/problem+json` for malformed/unparseable JSON
     - `422 application/problem+json` for validation errors (e.g., missing body)

  Notes on repo conventions (authoritative contracts):
   - The current codegen script (generate_inbound_models.sh) sources schemas from specs/001-service-skeleton/contracts/. For this feature, treat specs/001-service-skeleton/contracts/ as the single authoritative contract set for CI/codegen and implementation.

2. **Inbound schema/model alignment**
   - Create a Pydantic schema for “any JSON value” in `src/adapters/inbound/api/schemas/` that
     mirrors the `json_value.schema.json` contract.
   - Generate the Pydantic model via generate_inbound_models.sh (treat the generated file as the mirror of specs source-of-truth).
   - Prefer a root-style schema that permits object/array/primitives/null.

3. **Router handler**
   - Implement `POST /components` in `src/adapters/inbound/api/routers/components.py`.
   - Behavior:
     - Accept any JSON request body via the inbound schema.
     - Log the received payload exactly once per request.
       - Serialize to a string, truncate to the first 4096 characters, and include a truncation indicator.
     - Return `200` with the exact same parsed JSON as the response body.
   - Error behavior:
     - Malformed JSON is automatically converted by existing validation handler into `400` Problem Details.
     - Missing body is handled by existing validation handler as `422` Problem Details.

4. **Tests**
   - Add tests matching existing patterns under `tests/`:
     - JSON object payload echoes successfully.
     - JSON array payload echoes successfully.
     - Malformed JSON returns `400` with `application/problem+json`.
   - (Optional) Add a test that asserts large payloads do not break the endpoint.

5. **Verification**
   - Run `pytest`.
   - Run the existing contract drift check:
     - `./generate_inbound_models.sh`
     - `git diff --exit-code src/adapters/inbound/api/schemas`
   - Run `python check_core_purity.py` to ensure no forbidden imports reach `src/core/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

No constitution violations requiring justification.
