# Quickstart: Rename MongoDB Collection Names

**Branch**: 010-rename-collection-names  
**Date**: 2026-05-16

This quickstart verifies that dashed MongoDB collection names are replaced with underscore-based
names in the data access layer and Mongo-backed persistence tests while public API behavior remains
unchanged.

## Prerequisites

- Python 3.12+
- The project virtual environment at `.venv/`
- Docker available for MongoDB persistence tests via testcontainers

## Verify the targeted rename surface

Run a focused search over the outbound MongoDB adapters and Mongo-backed persistence tests:

```bash
cd /Users/ertant/work/vscode-projects/graph-service
rg 'application-architectures|micro-affinity-groups' \
  src/adapters/outbound/mongodb \
  tests/test_application_architectures_persistence.py \
  tests/test_micro_affinity_groups_persistence.py
```

Expected after implementation:

- No dashed collection identifiers remain in the outbound MongoDB adapters
- No dashed collection identifiers remain in the Mongo-backed persistence tests
- The underscore-based mapping is centralized in `src/adapters/outbound/mongodb/collection_names.py`

## Run the Mongo-backed persistence suites

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest \
  tests/test_application_architectures_persistence.py \
  tests/test_micro_affinity_groups_persistence.py \
  tests/test_component_dependencies_persistence.py \
  tests/test_components_persistence.py -v
```

Expected:

- Application architecture persistence tests pass using `application_architectures`
- Micro affinity group persistence tests pass using `application_architectures`,
  `micro_affinity_groups`, and `micro_affinity_groups_processed`
- Component persistence and dependency persistence tests continue passing unchanged

## Run the functional regression suite

```bash
cd /Users/ertant/work/vscode-projects/graph-service
/Users/ertant/work/vscode-projects/graph-service/.venv/bin/python -m pytest tests -v -k "not perf_smoke"
```

Expected:

- All functional tests pass after the collection rename
- No HTTP route or payload contract regressions occur
- Persistence-backed tests confirm the underscore-based collection names are wired correctly

## Verified planning baseline

The functional regression command above was run during planning in the active workspace and
completed successfully with:

- `81 passed`
- `3 deselected` (`perf_smoke`)

This baseline confirms the workspace is green before implementation of the collection rename.