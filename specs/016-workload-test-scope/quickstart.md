# Quickstart: Workload Test Scope Endpoint

## Goal

Validate the new test-scope endpoint behavior end-to-end, including source and destination
relationship traversal, environment isolation, unknown handling, ordering, summary math, and
error semantics.

## 1) Run New Endpoint-Focused Test Suites

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_workload_test_scope_use_case.py \
  tests/test_workload_test_scope_endpoint.py \
  tests/test_workload_test_scope_persistence.py -v
```

Expected coverage:

- source relationship traversal
- destination relationship traversal
- dual-role workload traversal with deduplication
- environment isolation (`production` vs `staging`)
- unknown workloads
- empty input list
- missing/blank environment returns `422`
- ambiguous workload ownership in same environment returns `422`
- malformed JSON returns `400` with problem-details payload
- summary calculations for distinct workloads and micro AGs
- response contract shape and snake_case keys

## 2) Run Existing Micro-Affinity Endpoint Regression Tests

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_micro_affinity_groups_endpoint.py \
  tests/test_micro_affinity_groups_persistence.py \
  tests/test_micro_affinity_group_use_case.py -v
```

Expected:

- no regressions in existing micro-affinity-group write and validation behavior

## 3) Run Core Purity Guard

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python check_core_purity.py
```

Expected:

- core purity check passes with no framework/driver imports in `src/core/`

## 4) Run Full Regression Suite

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v
```

Expected:

- all previously passing tests continue to pass
- new test-scope endpoint tests pass

## Manual Smoke Request (Optional)

```bash
curl -X POST \
  "http://127.0.0.1:8000/v1/micro-affinity-groups/workloads/test-scope?environment=preproduction" \
  -H "Content-Type: application/json" \
  -d '{"changed_workloads":[{"workload_asset_id":"asset_1"}]}'
```

Expected:

- response includes snake_case keys
- response includes `environment`, `changed_workloads`, `affected_workload_relationships`,
  `unknown_workloads`, and `summary`
- summary values match computed payload counts

## Execution Evidence

- Workload test-scope focused suites:

  ```bash
  /Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
    tests/test_workload_test_scope_use_case.py \
    tests/test_workload_test_scope_endpoint.py \
    tests/test_workload_test_scope_persistence.py -v
  ```

  Outcome: `19 passed`

- Existing micro-affinity regression suites:

  ```bash
  /Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
    tests/test_micro_affinity_groups_endpoint.py \
    tests/test_micro_affinity_groups_persistence.py \
    tests/test_micro_affinity_group_use_case.py -v
  ```

  Outcome: `34 passed`

- Core purity guard:

  ```bash
  /Users/ertant/work/vscode-projects/graph-service/.venv/bin/python check_core_purity.py
  ```

  Outcome: `Core purity check passed.`

- Full regression suite:

  ```bash
  /Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v
  ```

  Outcome: `132 passed, 4 skipped`

- Workload test-scope latency smoke validation (perf opt-in):

  ```bash
  GRAPH_SERVICE_RUN_PERF_SMOKE=1 /Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
    tests/test_perf_smoke_workload_test_scope.py -v
  ```

  Outcome: `1 passed` (p95 <= 300 ms, p99 <= 600 ms assertions passed)
