# Data Model: Service Architectural Skeleton

**Branch**: 001-service-skeleton  
**Date**: 2026-03-14  
**Input**: [spec.md](spec.md)

This feature is primarily scaffolding and wiring. The data model below captures the core domain concepts
that will guide port definitions and future use cases.

## Domain Entities (Core)

### Component

Represents a software component/node in the dependency graph.

- Fields:
  - `component_id` (string, immutable identifier)
  - `name` (string)
  - `version` (string, optional)
  - `metadata` (map/object, optional)
- Invariants:
  - `component_id` is non-empty and unique within a graph.

### DependencyEdge

Represents a directed dependency from one component to another.

- Fields:
  - `from_component_id` (string)
  - `to_component_id` (string)
  - `edge_type` (string, optional; e.g., runtime/dev/test)
  - `metadata` (map/object, optional)
- Invariants:
  - `from_component_id != to_component_id`.

### DependencyGraph

An aggregate representing the set of components and edges.

- Fields:
  - `components` (set/list of `Component`)
  - `edges` (set/list of `DependencyEdge`)
- Invariants:
  - Edge endpoints must reference existing components.

## Domain Exceptions (Core)

These are representative examples to guide the global error mapping skeleton.

- `ComponentNotFound` (context: `component_id`)
- `CircularDependencyDetected` (context: cycle path)
- `DuplicateDependencyEdge` (context: `from_component_id`, `to_component_id`)

## External Contract Entities (API)

### Problem Details (RFC 7807)

Standard error format for non-2xx responses.

- Required:
  - `type` (string; URI or identifier)
  - `title` (string)
  - `status` (int)
  - `detail` (string)
- Optional extensions:
  - `error_code` (string)
  - `errors` (object/array for validation details)

### HealthResponse

Minimal response entity for the health-check endpoint.

- Fields:
  - `status` (string; e.g., "ok")
  - `service` (string; service name)
  - `version` (string; build/version identifier)
  - `time` (string; ISO-8601)
