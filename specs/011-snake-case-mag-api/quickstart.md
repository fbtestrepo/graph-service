# Quickstart: Snake Case MAG API

**Branch**: 011-snake-case-mag-api  
**Date**: 2026-05-16

This quickstart verifies the planned migration of `POST /v1/micro-affinity-groups` from
kebab-case payloads to native `snake_case` request, response, and persistence documents.

## Prerequisites

- Python 3.12+
- The project virtual environment at `.venv/`
- Docker available for MongoDB persistence tests via testcontainers

## Verify the contract-source files targeted by the migration

```bash
cd /Users/ertant/work/vscode-projects/graph-service
rg 'micro-ag-id|parent-asset-id|architecture-version|effective-date|asset-id|source-workload|destination-workload' \
  specs/samples/micro-affinity-group \
  specs/001-service-skeleton/contracts/micro_affinity_group.schema.json \
  specs/001-service-skeleton/contracts/micro_affinity_group_processed.schema.json
```

Expected after implementation:

- No MAG request/response contract keys remain in kebab-case in those four files
- The sample documents and JSON Schemas describe the same `snake_case` field names

## Regenerate the inbound MAG models

```bash
cd /Users/ertant/work/vscode-projects/graph-service
./generate_inbound_models.sh
git diff -- src/adapters/inbound/api/schemas/micro_affinity_group.py \
  src/adapters/inbound/api/schemas/micro_affinity_group_processed.py
```

Expected after implementation:

- Generated MAG schema modules no longer use `Field(..., alias='...')` for renamed MAG keys
- The custom `MicroAffinityGroup` wrapper with the unique workload-id validator is still present

## Verify the runtime migration surface

```bash
cd /Users/ertant/work/vscode-projects/graph-service
rg 'micro-ag-id|parent-asset-id|architecture-version|effective-date|source-workload|destination-workload' \
  src/adapters/inbound/api/routers/micro_affinity_groups.py \
  src/core/use_cases/upsert_micro_affinity_group.py \
  src/adapters/outbound/mongodb/micro_affinity_group_repository.py \
  src/adapters/outbound/mongodb/micro_affinity_group_processed_repository.py \
  tests/test_micro_affinity_group_use_case.py \
  tests/test_micro_affinity_groups_endpoint.py \
  tests/test_micro_affinity_groups_persistence.py \
  tests/test_perf_smoke_micro_affinity_groups.py

rg 'asset-id|source-workload|destination-workload' \
  src/core/domain/micro_affinity_group_relationship_mapper.py \
  tests/test_micro_affinity_group_relationship_mapper.py
```

Expected after implementation:

- No MAG-specific kebab-case payload keys remain in the router, use case, mapper, repositories, or
  MAG-focused tests
- Application architecture fixtures may still contain their existing non-MAG field names such as
  `asset-id`, `relationship-type`, and `unique-id`

## Run the MAG-focused regression suites

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_micro_affinity_group_relationship_mapper.py \
  tests/test_micro_affinity_group_use_case.py \
  tests/test_micro_affinity_groups_endpoint.py \
  tests/test_micro_affinity_groups_persistence.py -v
```

Expected:

- Snake_case requests are accepted and kebab-case MAG payloads are rejected
- Successful endpoint responses use `snake_case` keys only
- Newly written raw and processed MongoDB documents use `snake_case` keys only

## Run the required functional regression suite

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v -k "not perf_smoke"
```

Expected:

- All functional tests pass without regressions in unrelated endpoints
- The MAG rename stays isolated to its contract, adapter, and persistence surfaces

## Optional perf-smoke verification

Run the MAG perf-smoke test only if its request fixture or response builders were updated during
implementation.

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_perf_smoke_micro_affinity_groups.py -v
```

Expected:

- The updated perf-smoke request and response helpers still use the final snake_case MAG contract
- This check is optional and does not replace the required non-perf functional regression suite

## Verified implementation results

The MAG snake_case migration was implemented and verified in the active workspace on 2026-05-16
with the following results:

- Focused MAG regression suite: `31 passed`
- Core purity check: `passed`
- Optional MAG perf-smoke suite: `1 passed`
- Required functional regression suite: `82 passed`
- Deselected tests during the required functional regression suite: `3` (`perf_smoke`)
