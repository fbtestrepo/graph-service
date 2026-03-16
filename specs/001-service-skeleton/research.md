# Research: Service Architectural Skeleton

**Branch**: 001-service-skeleton  
**Date**: 2026-03-14  
**Input**: [spec.md](spec.md)

This document captures Phase 0 research decisions required to scaffold the Dependency Graph Service API.

## Decisions

### 1) Error response standard

- Decision: Use RFC 7807 Problem Details (`application/problem+json`) for non-2xx responses, with an optional stable `error_code` extension.
- Rationale: Standardized client handling; consistent across validation errors and domain errors; avoids leaking internals.
- Alternatives considered:
  - FastAPI default `{ "detail": ... }`: too inconsistent across error types; lacks stable machine codes.
  - Custom envelope: workable but reinvents a standard and reduces interoperability.

### 2) Dependency Injection lifecycle

- Decision: App-singleton lifecycle for MongoDB and LDAP clients/adapters (create on startup, reuse per request, close on shutdown).
- Rationale: Avoids connection churn; aligns with typical driver/client expectations; simplifies resource management.
- Alternatives considered:
  - Per-request clients: higher overhead and more failure modes.
  - Per-use-case: unpredictable resource usage; harder to test.

### 3) Sync vs async boundaries

- Decision: Keep core ports and use cases synchronous; manage concurrency in the inbound adapter layer.
- Rationale: Keeps the core portable and test-friendly; avoids async leaking into domain abstractions.
- Alternatives considered:
  - Async core: increases complexity; forces async across many layers.
  - Hybrid: risks inconsistent calling conventions.

### 4) Core purity enforcement

- Decision: Add an automated import-boundary check in CI that fails if `src/core/` imports forbidden libraries (e.g., `fastapi`, `motor`/`pymongo`, `ldap3`).
- Rationale: Scales beyond code review; prevents accidental architectural drift.
- Alternatives considered:
  - Code review only: easy to miss in large PRs.
  - Manual grep: brittle but acceptable as an initial implementation if needed.

### 5) Specs-first model synchronization

- Decision: Generate inbound Pydantic models from source-of-truth schemas in `specs/`, commit generated code, and verify up-to-date in CI.
- Rationale: Minimizes drift; makes reviewable diffs; enforces SDD.
- Alternatives considered:
  - Manual models + contract tests: higher drift risk and more maintenance.
  - Generate-at-build only: fewer diffs but harder to review and debug.

## Notes / Open Items

- Python version baseline is set to 3.12 for scaffolding; if the environment requires a different version, adjust in `pyproject.toml` during implementation.
- Concrete schema-to-model tooling will be selected during implementation (the plan requires automation and CI verification, not a specific tool).
