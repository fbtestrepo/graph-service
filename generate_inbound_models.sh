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

"$PYTHON_BIN" -m datamodel_code_generator \
  --input "$CONTRACTS_DIR/micro_affinity_group_processed.schema.json" \
  --input-file-type jsonschema \
  --output "$OUT_DIR/micro_affinity_group_processed.py" \
  --disable-timestamp \
  --output-model-type pydantic_v2.BaseModel

"$PYTHON_BIN" -m datamodel_code_generator \
  --input "$CONTRACTS_DIR/micro_affinity_group.schema.json" \
  --input-file-type jsonschema \
  --output "$OUT_DIR/micro_affinity_group.py" \
  --disable-timestamp \
  --output-model-type pydantic_v2.BaseModel

"$PYTHON_BIN" -c "
from pathlib import Path

schema_path = Path(r'$OUT_DIR') / 'micro_affinity_group.py'
schema = schema_path.read_text(encoding='utf-8')
if 'class MicroAffinityGroup(BaseModel):' not in schema:
    raise SystemExit('Expected micro_affinity_group.py to contain class MicroAffinityGroup')
schema = schema.replace('class MicroAffinityGroup(BaseModel):', 'class MicroAffinityGroupDocument(BaseModel):', 1)
schema += '''

from pydantic import model_validator


class MicroAffinityGroup(MicroAffinityGroupDocument):
  @model_validator(mode='after')
  def _validate_unique_workload_ids(self) -> MicroAffinityGroup:
    seen: set[str] = set()
    duplicates: list[str] = []
    for workload in self.workloads:
      if workload.id in seen and workload.id not in duplicates:
        duplicates.append(workload.id)
      seen.add(workload.id)

    if duplicates:
      duplicate_list = ', '.join(sorted(duplicates))
      raise ValueError(f'workloads contain duplicate id values: {duplicate_list}')

    return self


__all__ = ['MicroAffinityGroup', 'MicroAffinityGroupDocument', 'MicroAffinityGroupWorkload']
'''
schema_path.write_text(schema, encoding='utf-8')
"

tmp_codegen_input_dir="$ROOT_DIR/tmp_codegen_application_architecture_input"
tmp_codegen_file="$ROOT_DIR/tmp_codegen_application_architecture.py"
rm -rf "$tmp_codegen_input_dir" "$tmp_codegen_file"
mkdir -p "$tmp_codegen_input_dir/schemas/calm"

cp "$CONTRACTS_DIR/application_architecture.schema.json" "$tmp_codegen_input_dir/application_architecture.schema.json"
cp -R "$ROOT_DIR/schemas/calm/v1_2" "$tmp_codegen_input_dir/schemas/calm/"

"$PYTHON_BIN" -c "
from pathlib import Path

contract_path = Path(r'$tmp_codegen_input_dir') / 'application_architecture.schema.json'
contract = contract_path.read_text(encoding='utf-8')
contract = contract.replace('../../../schemas/calm/v1_2/calm.json', './schemas/calm/v1_2/calm.json')
contract_path.write_text(contract, encoding='utf-8')
"

"$PYTHON_BIN" -m datamodel_code_generator \
  --input "$tmp_codegen_input_dir/application_architecture.schema.json" \
  --input-file-type jsonschema \
  --output "$tmp_codegen_file" \
  --disable-timestamp \
  --output-model-type pydantic_v2.BaseModel

if [ ! -f "$tmp_codegen_file" ]; then
  echo "Expected $tmp_codegen_file to be generated" >&2
  exit 1
fi

cp "$tmp_codegen_file" "$OUT_DIR/application_architecture.py"

"$PYTHON_BIN" -c "
from pathlib import Path

schema_path = Path(r'$OUT_DIR') / 'application_architecture.py'
schema = schema_path.read_text(encoding='utf-8')
schema += '''

from pydantic import field_validator, model_validator


class ApplicationArchitecture(ApplicationArchitectureDocument):
  model_config = ConfigDict(extra='forbid')

  @model_validator(mode='before')
  @classmethod
  def _validate_root_metadata_object(cls, data: Any) -> Any:
    if not isinstance(data, dict):
      return data

    metadata = data.get('metadata')
    if metadata is None:
      raise ValueError('metadata is required')
    if not isinstance(metadata, dict):
      raise ValueError('metadata must be an object')

    return data

  @field_validator('metadata')
  @classmethod
  def _validate_metadata(cls, value: Metadata) -> Metadata:
    if not value.AssetID.isalnum():
      raise ValueError('AssetID must contain only ASCII letters and digits')

    version_parts = value.version.split('.')
    if len(version_parts) != 3 or any(not part.isdigit() for part in version_parts):
      raise ValueError('version must use major.minor.patch semantic version format')

    if not isinstance(value.created, date):
      raise ValueError('created must be a valid calendar date')

    return value


__all__ = ['ApplicationArchitecture', 'ApplicationArchitectureDocument', 'Metadata']
'''
schema_path.write_text(schema, encoding='utf-8')
"

rm -rf "$tmp_codegen_input_dir" "$tmp_codegen_file"

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
