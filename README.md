
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

Generated inbound models live under `src/adapters/inbound/api/schemas/` and are sourced from JSON Schemas in `specs/001-service-skeleton/contracts/`.

```bash
./generate_inbound_models.sh
git diff --exit-code src/adapters/inbound/api/schemas
```

## CI Enforces

- `python -m compileall src`
- `python check_core_purity.py`
- `./generate_inbound_models.sh` + drift check for `src/adapters/inbound/api/schemas`
- `pytest`

