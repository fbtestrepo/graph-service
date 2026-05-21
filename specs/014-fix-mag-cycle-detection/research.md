# Research: Fix MAG Cycle Detection

## Decision 1: Replace global SCC candidate selection with path-scoped back-edge detection

- **Decision**: Detect cyclic edges from the active root-scoped traversal path used to resolve the
  deployment-scope graph, rather than selecting a bypass edge from all edges in a strongly
  connected component.
- **Rationale**:
  - The reported defect shows that global SCC membership over-identifies candidate edges and then
    lets lexicographic ordering choose a non-cyclic downstream edge.
  - The feature specification defines the cyclic edge as one that points to a MAG already on the
    current traversal path after the one-hop-upstream boundary has been established.
  - Path-scoped detection matches the expected correction for the reported graph rooted at `C`,
    where `E1 -> C` is the true back-edge and `C -> D` is not.
- **Alternatives considered**:
  - Keep Tarjan SCC detection and change the sort rule: rejected because the wrong candidate set is
    the root problem.
  - Mark every edge inside the SCC as cyclic: rejected because it would over-report cyclic edges
    and distort deployment-stage calculation.

## Decision 2: Preserve the existing endpoint contract and document a behavior-only correction

- **Decision**: Keep the request and response schema unchanged and document the fix as a behavioral
  correction to cyclic-edge marking and deployment-stage generation.
- **Rationale**:
  - The defect does not require any new fields, removed fields, or shape changes in the endpoint
    response.
  - Existing contracts already support `is_cyclic` and `bypassed_edges`; only the edge chosen for
    those fields changes.
  - Limiting the change to behavior avoids unnecessary schema churn and reduces regression risk.
- **Alternatives considered**:
  - Add a new response field describing traversal path: rejected because it exceeds the scope of
    the defect and changes the public contract unnecessarily.
  - Update root-level canonical schemas: rejected because this endpoint uses feature-local
    contracts and the defect does not alter shared data contracts.

## Decision 3: Recompute deployment stages from only the reduced graph after removing true back-edges

- **Decision**: Continue to compute deployment stages from the reduced graph, but remove only the
  path-scoped cyclic edges identified during traversal.
- **Rationale**:
  - The current deployment-stage error is downstream of the wrong edge being bypassed.
  - Once the system bypasses only `E1 -> C` for the reported graph, the reduced graph naturally
    yields the expected five stages.
  - This preserves the existing mental model for deployment layers and avoids mixing traversal and
    stage-reduction semantics.
- **Alternatives considered**:
  - Special-case the reported graph in deployment-stage logic: rejected because the defect is
    algorithmic and must generalize to other cyclic graphs.
  - Recompute stages from a separate hand-authored cycle-free graph: rejected because it would
    duplicate existing graph-reduction logic.

## Decision 4: Add targeted regression coverage at all three existing deployment-scope layers

- **Decision**: Add the reported graph as a regression scenario in use-case, endpoint, and
  persistence tests, then run the full suite.
- **Rationale**:
  - The defect is externally visible at the API level but originates in core graph logic.
  - The repository already tests deployment-scope behavior at the use-case, endpoint, and
    persistence layers, so the new regression should follow the same structure.
  - The user explicitly requested proof that the specific scenario is fixed and that no regressions
    occur in the broader suite.
- **Alternatives considered**:
  - Add only a single unit test: rejected because it does not protect the endpoint or persistence
    integration paths.
  - Rely only on full-suite regression: rejected because the reported graph is not currently covered.