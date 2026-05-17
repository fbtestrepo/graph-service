# Quickstart: MAG Upsert Uniqueness

**Branch**: 012-mag-upsert-uniqueness  
**Date**: 2026-05-17

This quickstart verifies the planned change to narrow MAG write identity to
`micro_ag_id + environment` while preserving `architecture_version` validation and response shape.

## Prerequisites

- Python 3.12+
- The project virtual environment at `.venv/`
- Docker available for MongoDB-backed tests via testcontainers

## Inspect the current identity surfaces

```bash
cd /Users/ertant/work/vscode-projects/graph-service
rg 'architecture_version.*(environment|micro_ag_id)|micro_ag_id.*architecture_version|environment.*architecture_version' \
  src/core \
  src/adapters/outbound/mongodb \
  tests/test_micro_affinity_group_use_case.py \
  tests/test_micro_affinity_groups_endpoint.py \
  tests/test_micro_affinity_groups_persistence.py \
  tests/test_perf_smoke_micro_affinity_groups.py
```

Expected after implementation:

- MAG write identity logic no longer depends on `architecture_version`
- `architecture_version` remains present in payload validation and application-architecture lookup

## Verify contract and generated model alignment

If service-local MAG contract wording or descriptions are updated, regenerate the inbound models.

```bash
cd /Users/ertant/work/vscode-projects/graph-service
./generate_inbound_models.sh
git diff -- \
  src/adapters/inbound/api/schemas/micro_affinity_group.py \
  src/adapters/inbound/api/schemas/micro_affinity_group_processed.py
```

Expected after implementation:

- The generated MAG schemas still require `architecture_version`
- Any updated identity wording in the source contracts is reflected in generated comments or
  wrappers without changing the field set unexpectedly

## Run focused MAG regression suites

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_micro_affinity_group_use_case.py \
  tests/test_micro_affinity_groups_endpoint.py \
  tests/test_micro_affinity_groups_persistence.py -v
```

Expected after implementation:

- Same `micro_ag_id + environment` with a changed `architecture_version` returns `200 OK`
- Different environments still coexist as separate records
- Pre-seeded duplicate records for one identity pair return `409 Conflict`
- Partial existing state in only one MAG collection is repaired and returns `200 OK`
- Raw and processed collections are fully replaced rather than merged
- Processed-write failures still roll back both collections

## Run the architecture guard

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python check_core_purity.py
```

Expected after implementation:

- The core remains free of FastAPI, pymongo/motor, and ldap3 imports

## Run the required non-perf regression suite

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v -k "not perf_smoke"
```

Expected after implementation:

- The required non-perf regression suite passes without regression loops
- MAG endpoint behavior remains contract-compliant across unit, endpoint, persistence, and perf
  coverage

## Optional targeted duplicate-conflict check

After implementation, use the new persistence-backed duplicate test to confirm that corrupted
pre-existing state is rejected cleanly.

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_micro_affinity_groups_persistence.py -k duplicate -v
```

Expected after implementation:

- The endpoint returns `409 Conflict`
- Neither raw nor processed documents are modified when duplicates already exist