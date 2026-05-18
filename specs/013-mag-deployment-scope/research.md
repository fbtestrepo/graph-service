# Research: MAG Deployment Scope

**Branch**: 013-mag-deployment-scope  
**Date**: 2026-05-17

## Decisions

### Decision 1: Resolve MAG dependencies one hop at a time with bounded Mongo-backed frontier expansion

- **Decision**: Build the graph through a reusable core traversal loop that expands one hop at a
  time, using batched MongoDB queries against `micro_affinity_groups_processed` for each frontier
  rather than loading the full collection into memory.
- **Rationale**:
  - The feature request explicitly prohibits whole-database in-memory loading.
  - The existing component-dependency use case already demonstrates that bounded frontier
    traversal fits the service architecture.
  - Per-hop batching preserves strict hop counting, isolates environment filters, and keeps the
    repository interface reusable for future MAG graph endpoints.
- **Alternatives considered**:
  - Load the full processed MAG collection into memory and join there: rejected because it violates
    the performance and query-locality requirements.
  - Encode the entire traversal in one oversized recursive aggregation pipeline: rejected because
    the workload-to-MAG join and 30-hop control become harder to reason about, test, and reuse.

### Decision 2: Derive MAG-to-MAG edges by matching destination workload asset ownership in the same environment

- **Decision**: Treat each processed MAG document as the owner of its `workloads[*].asset_id`
  values, then resolve every `relationships[*].destination_workload.asset_id` to at most one target
  processed MAG in the same environment.
- **Rationale**:
  - The source MAG is explicit in the document being traversed; only the destination MAG must be
    discovered indirectly.
  - Matching on asset ownership is the rule given in the plan request and can be expressed with an
    optimized Mongo query filtered by `environment`.
  - Environment-scoped ownership resolution prevents cross-environment contamination when identical
    workloads exist elsewhere.
- **Alternatives considered**:
  - Match destinations on `destination_workload.id` alone: rejected because the user specified the
    asset-based ownership rule.
  - Emit self-referential MAG edges when source and destination workloads belong to the same MAG:
    rejected because the plan request requires intra-group suppression.

### Decision 3: Implement repository-level environment and asset lookup methods instead of generic full-document scans

- **Decision**: Extend the processed-MAG repository port with targeted read capabilities for root
  lookup and environment-scoped destination-asset matching, including lean projections that return
  only the fields needed for graph resolution.
- **Rationale**:
  - The core needs to reason about roots, destination ownership, and per-hop edges without knowing
    MongoDB query syntax.
  - Focused port methods keep the adapter efficient and allow later optimization with aggregation,
    indexes, or projections without touching the use case.
  - Lean reads minimize payload transfer and make it practical to traverse large graphs up to the
    30-hop boundary.
- **Alternatives considered**:
  - Add a repository method that returns every processed MAG in an environment: rejected because it
    recreates an in-memory graph load.
  - Query MongoDB directly from the use case: rejected because it violates the hexagonal boundary.

### Decision 4: Separate resolved graph construction from cycle reduction and deployment sequencing

- **Decision**: Compute the full resolved MAG edge set first, then run deterministic cycle
  reduction and deployment-step generation as separate pure-core phases.
- **Rationale**:
  - The response must show both the complete `dependency_graph` and the reduced deployment graph,
    so cycle handling cannot be mixed into initial edge discovery.
  - This separation makes the graph builder reusable by future endpoints that need the resolved
    graph but not the deployment sequence.
  - Pure-core post-processing is straightforward to unit test without MongoDB fixtures.
- **Alternatives considered**:
  - Drop cycle edges during traversal: rejected because the response must still surface the
    cycle-completing back-edge with `is_cyclic = true`.
  - Build deployment steps directly during traversal: rejected because step generation depends on
    the final reduced graph, not frontier order.

### Decision 5: Reconcile cycle semantics by identifying hierarchy back-edges, then applying deterministic ordering

- **Decision**: Detect cycles in the resolved graph, identify the back-edge as the edge from the
  deepest downstream node back toward the highest upstream node in the resolved scope, and use
  lexicographic ordering by `(source_micro_ag_id, destination_micro_ag_id)` to break ties between
  equivalent cycle-breaking candidates.
- **Rationale**:
  - The plan request requires the sample cycle queried at `C` to mark `A -> B` as the cyclic edge
    because `B` is the upstream boundary and `A` is the deepest downstream node in the scope.
  - The feature spec already clarified that output ordering and repeated results must be
    deterministic.
  - Combining resolved-scope hierarchy with lexicographic tie-breaking satisfies both the sample
    semantics and the deterministic-contract requirement.
- **Alternatives considered**:
  - Choose the first cycle edge encountered during traversal: rejected because runtime traversal
    order is explicitly not the contract.
  - Choose an arbitrary lexicographically smallest edge from the whole graph without hierarchy:
    rejected because it does not guarantee the sample’s notion of the back-edge.

### Decision 6: Generate deployment steps dependency-first from the reduced DAG

- **Decision**: Interpret `A -> B` as `A` depends on `B`, so deployment Layer 1 is the set of MAGs
  with no outgoing dependency edges in the reduced DAG, and later layers are built iteratively as
  those dependencies are removed.
- **Rationale**:
  - This matches the feature clarification and the sample output where `A` deploys before `E`,
    then `D`, then `C`, then `B` after `A -> B` has been bypassed.
  - Grouping all simultaneously deployable MAGs into the same step preserves the endpoint’s
    parallel deployment requirement.
  - Lexicographic ordering inside each step keeps regression assertions stable.
- **Alternatives considered**:
  - Use incoming-edge zero nodes as Layer 1: rejected because it reverses the required dependency
    semantics for this graph model.
  - Force the requested root MAG to appear first: rejected because it would violate dependency
    ordering whenever the root depends on downstream MAGs.

### Decision 7: Author feature-local response contracts now and defer codegen wiring to implementation

- **Decision**: Create a feature-local OpenAPI contract and modular JSON Schemas under
  `specs/013-mag-deployment-scope/contracts/`, including the deployment-scope response, edge,
  sequence, and step schemas, while documenting that later implementation may need to stage or
  wire these schemas into the existing generator pipeline rooted at `specs/001-service-skeleton/contracts/`.
- **Rationale**:
  - The feature explicitly requires a Pydantic response model and code-generation consideration.
  - The repo’s current codegen pipeline is optimized around service-local JSON Schema contracts.
  - Creating the contracts now lets implementation choose between extending the generator or
    staging the new schema into the current contract root without changing the feature intent.
- **Alternatives considered**:
  - Handwrite the Pydantic response model only in code: rejected because it bypasses the repo’s
    contracts-first workflow.
  - Delay schema authoring until implementation: rejected because the plan phase must define the
    external interface contract.

## Open Questions

None. The spec clarifications and design research are sufficient for task generation.