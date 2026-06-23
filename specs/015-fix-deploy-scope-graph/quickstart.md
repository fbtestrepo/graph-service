# Quickstart: Deploy-Scope Graph Resolution Fix

## Goal

Validate that deploy-scope now resolves complete downstream graphs from one-hop upstream seeds,
marks only path back-edges as cyclic, preserves existing contracts, and introduces no regressions.

## 1) Run Targeted Deployment-Scope Regression Suites

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_micro_affinity_group_deployment_scope_use_case.py \
  tests/test_micro_affinity_group_deployment_scope_endpoint.py \
  tests/test_micro_affinity_group_deployment_scope_persistence.py -v
```

Expected:

- Root `C` case includes full expected graph, with only the expected cyclic edge flagged per spec.
- Root `E3` case includes expected graph and cycle behavior per spec.
- `deployment_sequence.bypassed_edges` contains only detected path back-edges.
- Deployment steps are deterministic and match expected layering.

## 2) Verify Error-Semantics Regressions

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_micro_affinity_group_deployment_scope_endpoint.py -k "404 or 422" -v
```

Expected:

- Missing root resource returns `404 Not Found`.
- Existing root with unresolved downstream graph returns `422 Unprocessable Entity`.

## 3) Run Core Purity Guard

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python check_core_purity.py
```

Expected:

- Core purity passes with no framework or driver imports leaking into `src/core/`.

## 4) Run Full Regression Suite

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v
```

Expected:

- All tests pass with no regressions in non-deploy-scope behavior.
- Ordering-sensitive assertions remain stable across repeated runs.

## Implementation Notes For Review

- Keep graph traversal, cycle detection, and ordering logic modular in core domain/use-case code.
- Do not hardcode sample graph constants or root-specific special cases.
- Preserve existing endpoint path and response schema shape.

## Verified Execution Notes

Date: 2026-06-20

- Targeted deploy-scope suites:
  - Command: `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests/test_micro_affinity_group_deployment_scope_use_case.py tests/test_micro_affinity_group_deployment_scope_endpoint.py tests/test_micro_affinity_group_deployment_scope_persistence.py -v`
  - Result: `26 passed`
- Focused 404/422 endpoint semantics:
  - Command: `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests/test_micro_affinity_group_deployment_scope_endpoint.py -k "404 or 422" -v`
  - Result: `2 passed, 5 deselected`
- Core purity guard:
  - Command: `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python check_core_purity.py`
  - Result: `Core purity check passed`
- Full regression suite:
  - Command: `/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v`
  - Result: `113 passed, 3 skipped`
