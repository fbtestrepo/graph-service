#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTRACTS_DIR="$ROOT_DIR/specs/001-service-skeleton/contracts"
OUT_DIR="$ROOT_DIR/src/adapters/inbound/api/schemas"

PYTHON_BIN="${PYTHON:-}"
if [ -z "$PYTHON_BIN" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  else
    PYTHON_BIN="python"
  fi
fi

"$PYTHON_BIN" -m datamodel_code_generator \
  --input "$CONTRACTS_DIR/component.schema.json" \
  --input-file-type jsonschema \
  --output "$OUT_DIR/component.py" \
  --disable-timestamp \
  --output-model-type pydantic_v2.BaseModel

"$PYTHON_BIN" -m datamodel_code_generator \
  --input "$CONTRACTS_DIR/problem_details.schema.json" \
  --input-file-type jsonschema \
  --output "$OUT_DIR/problem_details.py" \
  --disable-timestamp \
  --output-model-type pydantic_v2.BaseModel

"$PYTHON_BIN" -m datamodel_code_generator \
  --input "$CONTRACTS_DIR/health_response.schema.json" \
  --input-file-type jsonschema \
  --output "$OUT_DIR/health_response.py" \
  --disable-timestamp \
  --output-model-type pydantic_v2.BaseModel

"$PYTHON_BIN" -m datamodel_code_generator \
  --input "$CONTRACTS_DIR/json_value.schema.json" \
  --input-file-type jsonschema \
  --output "$OUT_DIR/json_value.py" \
  --disable-timestamp \
  --output-model-type pydantic_v2.BaseModel
