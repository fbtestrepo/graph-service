
# graph-service

Dependency Graph Service (architectural skeleton).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e '.[dev]'
```

## Run (development)

```bash
uvicorn src.infrastructure.main:create_app --factory --reload --port 8000
```

## HTTP Routes

Business endpoints are published under the `/v1` prefix:

- `POST /v1/components/validate`
- `POST /v1/components`
- `GET /v1/components/{component_id}`
- `GET /v1/components/{node_id}/dependencies`
- `POST /v1/application-architectures`
- `POST /v1/micro-affinity-groups`

Infrastructure and documentation routes remain at the root path:

- `GET /health`
- `GET /openapi.json`
- `GET /docs`
- `GET /redoc`

Former root business paths such as `/components` and `/micro-affinity-groups` are no longer part
of the supported route surface.

## Error Semantics

- `404 Not Found` is reserved for the primary resource identified directly by the request path not
	existing in persistence.
- `422 Unprocessable Entity` is used for request-schema validation failures and for
	graph-traversal/data-integrity failures where the primary path resource exists but downstream
	resolution cannot be completed consistently.
- Graph-traversal endpoints must not return `404` for broken downstream dependencies once the root
	resource has been confirmed to exist.

## Tests

```bash
pytest
```

## Schema → Model Codegen

Feature intent, behavioral requirements, and software specifications live under `specs/`.
Canonical data contracts live under `schemas/` (for example, `schemas/calm/v1_2/`).
Generated inbound models live under `src/adapters/inbound/api/schemas/` and are currently sourced
from the authoritative API contract schemas in `specs/001-service-skeleton/contracts/`.

The CALM application architecture endpoint uses a service-level wrapper contract in
`specs/001-service-skeleton/contracts/application_architecture.schema.json` that references the
canonical CALM entry schema in `schemas/calm/v1_2/calm.json` and adds the required root
`metadata.AssetID`, `metadata.version`, and `metadata.created` constraints.

The micro affinity group endpoint uses
`specs/001-service-skeleton/contracts/micro_affinity_group.schema.json` as its authoritative
service contract, and the enriched success response uses
`specs/001-service-skeleton/contracts/micro_affinity_group_processed.schema.json`.
Generated schema code is extended with a stable wrapper in
`src/adapters/inbound/api/schemas/micro_affinity_group.py` so duplicate workload IDs are rejected
before the core use case runs; the processed response model is generated into
`src/adapters/inbound/api/schemas/micro_affinity_group_processed.py`.

The `POST /micro-affinity-groups` flow now performs a transactional dual write:

- raw validated payloads are stored in `micro-affinity-groups`
- relationship-enriched projections are stored in `micro-affinity-groups-processed`
- both writes share one MongoDB transaction, so processed-write failures roll back the raw write

```bash
./generate_inbound_models.sh
git diff --exit-code src/adapters/inbound/api/schemas
```

## CI Enforces

- `python -m compileall src`
- `python check_core_purity.py`
- `./generate_inbound_models.sh` + drift check for `src/adapters/inbound/api/schemas`
- `pytest`

Targeted micro-affinity-group verification:

```bash
pytest tests/test_micro_affinity_groups_endpoint.py \
	tests/test_micro_affinity_group_relationship_mapper.py \
	tests/test_micro_affinity_group_use_case.py \
	tests/test_micro_affinity_groups_persistence.py
GRAPH_SERVICE_RUN_PERF_SMOKE=1 pytest tests/test_perf_smoke_micro_affinity_groups.py
```

