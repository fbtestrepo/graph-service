
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

```bash
./generate_inbound_models.sh
git diff --exit-code src/adapters/inbound/api/schemas
```

## CI Enforces

- `python -m compileall src`
- `python check_core_purity.py`
- `./generate_inbound_models.sh` + drift check for `src/adapters/inbound/api/schemas`
- `pytest`

