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
  --input "$CONTRACTS_DIR/component_node.schema.json" \
  --input-file-type jsonschema \
  --output "$OUT_DIR/component_node.py" \
  --disable-timestamp \
  --output-model-type pydantic_v2.BaseModel

tmp_codegen_dir="$ROOT_DIR/tmp_codegen_component_dependencies_response"
rm -rf "$tmp_codegen_dir"
mkdir -p "$tmp_codegen_dir"

"$PYTHON_BIN" -m datamodel_code_generator \
  --input "$CONTRACTS_DIR/component_dependencies_response.schema.json" \
  --input-file-type jsonschema \
  --output "$tmp_codegen_dir" \
  --disable-timestamp \
  --output-model-type pydantic_v2.BaseModel

if [ ! -f "$tmp_codegen_dir/__init__.py" ]; then
  echo "Expected $tmp_codegen_dir/__init__.py to be generated" >&2
  exit 1
fi

if [ ! -f "$tmp_codegen_dir/dependency_edge.py" ]; then
  echo "Expected $tmp_codegen_dir/dependency_edge.py to be generated" >&2
  exit 1
fi

cp "$tmp_codegen_dir/__init__.py" "$OUT_DIR/component_dependencies_response.py"
cp "$tmp_codegen_dir/dependency_edge.py" "$OUT_DIR/dependency_edge.py"

"$PYTHON_BIN" -c "
from pathlib import Path

edge_path = Path(r'$OUT_DIR') / 'dependency_edge.py'
resp_path = Path(r'$OUT_DIR') / 'component_dependencies_response.py'

edge = edge_path.read_text(encoding='utf-8')
if 'class Schema(' not in edge:
    raise SystemExit('Expected dependency_edge.py to contain class Schema')
edge = edge.replace('class Schema(', 'class DependencyEdge(')
edge_path.write_text(edge, encoding='utf-8')

resp = resp_path.read_text(encoding='utf-8')
if 'dependency_edge.Schema' not in resp:
    raise SystemExit('Expected component_dependencies_response.py to reference dependency_edge.Schema')
resp = resp.replace('dependency_edge.Schema', 'dependency_edge.DependencyEdge')
resp_path.write_text(resp, encoding='utf-8')
"

rm -rf "$tmp_codegen_dir"

"$PYTHON_BIN" -m datamodel_code_generator \
  --input "$CONTRACTS_DIR/json_value.schema.json" \
  --input-file-type jsonschema \
  --output "$OUT_DIR/json_value.py" \
  --disable-timestamp \
  --output-model-type pydantic_v2.BaseModel
