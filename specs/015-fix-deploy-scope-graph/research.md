# Research: Deploy-Scope Graph Resolution Fix

## Decision 1: Seed downstream traversal from one-hop upstream dependents (with root fallback)

- **Decision**: For a requested root MAG, first collect exactly one-hop upstream dependents, then
  start downstream traversal from that seed set. If the seed set is empty, traverse downstream
  starting from the root MAG.
- **Rationale**:
  - This directly addresses the missing-edge defect where downstream dependencies reachable from
    immediate upstream dependents were excluded.
  - It preserves the one-hop upstream boundary while still producing complete downstream closure.
  - Root fallback avoids empty traversal for valid roots with no upstream dependents.
- **Alternatives considered**:
  - Start traversal from root only: rejected because it misses required branches seeded via
    immediate upstream dependents.
  - Recurse upstream beyond one hop: rejected because it violates the feature contract.

## Decision 2: Use path-scoped back-edge detection with explicit visited initialization

- **Decision**: Classify an edge as cyclic only when its destination already appears on the current
  branch path-sequenced visited list. Initialize that visited list with the requested root plus all
  immediate upstream dependents before downstream DFS.
- **Rationale**:
  - This matches the clarified feature rule and resolves ambiguity between global-visited and
    branch-path behavior.
  - It reproduces expected sample outcomes for root `C` and root `E3`.
  - It prevents false-positive cycle tagging on edges that are merely revisited through other
    branches but not back-edges on the active path.
- **Alternatives considered**:
  - Global cycle detection with SCC-wide edge selection: rejected because it can mark incorrect
    edges as cyclic for this endpoint contract.
  - Pure DFS-path initialization without upstream preload: rejected because it conflicts with the
    clarified behavior used to match expected outputs.

## Decision 3: Keep topological layering algorithm, exclude only bypassed cyclic edges

- **Decision**: Preserve current deployment-step layering logic and build steps from the reduced
  graph produced by removing only detected cyclic back-edges.
- **Rationale**:
  - The issue is in graph resolution/cycle identification, not in the layering algorithm itself.
  - Preserving the layering logic minimizes regression risk and aligns with user constraints.
  - This keeps implementation modular and avoids hardcoded scenario-specific logic.
- **Alternatives considered**:
  - Rewrite topological layering algorithm: rejected as out of scope and unnecessary.
  - Special-case known sample graphs: rejected due to maintainability and review constraints.

## Decision 4: Make output ordering deterministic with cyclic-aware dependency_graph ordering

- **Decision**: Keep response ordering contractual as clarified:
  - `deployment_sequence.steps` sorted by `step_index` ascending
  - `micro_ag_ids` sorted lexicographically inside each step
  - `dependency_graph` sorted as non-cyclic edges first (lexicographic by
    `(source_micro_ag_id, destination_micro_ag_id)`), followed by cyclic edges with the same
    lexicographic sort.
- **Rationale**:
  - Deterministic ordering stabilizes tests and client integrations.
  - Cyclic-aware hybrid ordering preserves sample-output compatibility.
- **Alternatives considered**:
  - Pure lexicographic ordering regardless of cyclic flag: rejected because it can diverge from
    expected contract shape.
  - Non-contractual ordering: rejected because it increases flakiness and ambiguity.

## Decision 5: Preserve endpoint/error contracts and verify with targeted + full regression tests

- **Decision**: Keep endpoint path and response schema unchanged; preserve traversal error
  semantics (`404` for missing root path resource, `422` for downstream resolution failures once
  root exists). Add/adjust targeted tests for root `C` and root `E3`, then run full suite.
- **Rationale**:
  - This is a behavior fix behind an existing API contract.
  - Contract stability lowers integration risk and fits constitution rules.
  - Full-suite execution validates no regressions in adjacent features.
- **Alternatives considered**:
  - Introduce new endpoint or response fields: rejected as unnecessary scope expansion.
  - Only run targeted tests: rejected because full-suite no-regression verification is required.
