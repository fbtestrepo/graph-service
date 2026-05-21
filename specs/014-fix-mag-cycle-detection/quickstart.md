# Quickstart: Fix MAG Cycle Detection

## Goal

Verify that cyclic deployment-scope resolution now identifies the path-scoped back-edge correctly
for the reported graph and that the fix does not regress existing behavior.

## Targeted Regression Tests

Run the deployment-scope suites after adding the reported graph coverage:

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_micro_affinity_group_deployment_scope_use_case.py \
  tests/test_micro_affinity_group_deployment_scope_endpoint.py \
  tests/test_micro_affinity_group_deployment_scope_persistence.py -v
```

Expected results:

- the reported graph rooted at `C` marks `E1 -> C` as the only cyclic edge
- `C -> D` remains in `dependency_graph` as a non-cyclic edge
- the deployment sequence contains five stages:
  - `E1`, `E2`, `E3`
  - `E`
  - `D`
  - `C`
  - `A`, `B`
- existing acyclic deployment-scope scenarios remain unchanged

## Architecture Guard

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python check_core_purity.py
```

Expected result:

- deployment-scope cycle logic remains isolated in `src/core/` with no framework or driver imports

## Full Regression Suite

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v
```

Expected result:

- the reported cyclic regression passes
- existing non-cyclic graph scenarios still pass
- no unrelated endpoint, persistence, or infrastructure regressions are introduced

## Verified Execution Notes

Verified in the repository workspace with the configured venv interpreter:

- targeted deployment-scope suites: `17 passed` in `2.65s`
- explicit deployment-scope `404` versus `422` regression pass: `12 passed, 1 deselected` in `0.13s`
- architecture guard: `Core purity check passed.`
- full regression suite: `104 passed, 3 skipped` in `4.60s`