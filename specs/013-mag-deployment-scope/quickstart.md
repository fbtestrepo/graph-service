# Quickstart: MAG Deployment Scope

**Branch**: 013-mag-deployment-scope  
**Date**: 2026-05-17

This quickstart verifies the planned deployment-scope endpoint for processed Micro-AG data,
including environment-scoped MAG edge resolution, cycle handling, deterministic deployment
sequencing, and the required full-test regression path.

## Prerequisites

- Python 3.12+
- Project virtual environment at `.venv/`
- Docker available for MongoDB-backed persistence tests

## Inspect the current MAG surfaces that the feature will extend

```bash
cd /Users/ertant/work/vscode-projects/graph-service
rg 'micro_affinity_group_processed|micro_affinity_groups_processed|relationships|deployment-scope' \
  src/adapters/inbound/api \
  src/core \
  src/adapters/outbound/mongodb \
  tests
```

Expected after implementation:

- The existing MAG router exposes a new GET deployment-scope endpoint under `/v1`
- The processed-MAG repository exposes targeted read methods for graph traversal
- New deployment-scope tests and response schema modules are present

## Review the response contract sample

```bash
cd /Users/ertant/work/vscode-projects/graph-service
cat specs/samples/micro-affinity-group/deployment-scope.json
```

Expected after implementation:

- The sample file remains the runtime source of truth for snake_case field names and stable
  ordering expectations
- The runtime response shape matches the sample’s top-level keys
- `dependency_graph`, `deployment_sequence.bypassed_edges`, and `steps[*].micro_ag_ids` are
  deterministic and snake_case

## Run focused deployment-scope unit and endpoint tests

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_micro_affinity_group_deployment_scope_use_case.py \
  tests/test_micro_affinity_group_deployment_scope_endpoint.py \
  tests/test_micro_affinity_group_deployment_scope_persistence.py -v
```

Expected after implementation:

- Linear chain traversal returns exactly one upstream inverse hop plus full downstream edges
- Branching graphs resolve without duplicate MAG edges
- A 35-node chain truncates gracefully at exactly 30 hops
- The sample cycle queried at `C` marks `A -> B` as cyclic and bypasses it in deployment
  sequencing
- Environment-specific joins resolve only target MAGs in the requested environment
- Internal source/destination relationships inside the same MAG do not emit self edges

## Run the architecture guard

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python check_core_purity.py
```

Expected after implementation:

- The new graph and deployment sequencing logic remains framework-agnostic in `src/core/`

## Run the full regression suite

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v
```

Expected after implementation:

- All existing endpoint and persistence suites still pass
- New deployment-scope tests pass without regressing MAG upsert behavior or unrelated routes

## Verified implementation commands

The following commands were run successfully during implementation verification:

```bash
cd /Users/ertant/work/vscode-projects/graph-service
./generate_inbound_models.sh
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_micro_affinity_group_deployment_scope_use_case.py \
  tests/test_micro_affinity_group_deployment_scope_endpoint.py \
  tests/test_micro_affinity_group_deployment_scope_persistence.py -v
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python check_core_purity.py
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v
```

## Optional targeted API verification

```bash
curl -i -sS "http://localhost:8000/v1/micro-affinity-groups/C/deployment-scope?environment=preproduction"
```

Expected after implementation:

- `200 OK` for an existing processed MAG and environment pair
- `application/json` response using snake_case only
- `dependency_graph` contains the expected MAG edges in lexicographic order
- `deployment_sequence.steps` groups parallel MAGs together and orders step contents
  lexicographically

## Optional error-path verification

```bash
curl -i -sS "http://localhost:8000/v1/micro-affinity-groups/does-not-exist/deployment-scope?environment=preproduction"
```

Expected after implementation:

- `404 Not Found` with `application/problem+json` when the root pair is missing
- `422 Unprocessable Entity` with `application/problem+json` when the root exists but a required
  downstream join is missing or ambiguous