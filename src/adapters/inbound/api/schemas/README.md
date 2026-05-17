# Inbound API Schemas (Generated)

This directory contains Pydantic models generated from the authoritative API contract schemas in
`specs/001-service-skeleton/contracts/`.

Canonical shared data contracts live separately under the repository root `schemas/` directory.

Schema-to-model mapping:

- `specs/001-service-skeleton/contracts/component.schema.json` → `src/adapters/inbound/api/schemas/component.py`
- `specs/001-service-skeleton/contracts/application_architecture.schema.json` → `src/adapters/inbound/api/schemas/application_architecture.py`
- `specs/001-service-skeleton/contracts/micro_affinity_group.schema.json` → `src/adapters/inbound/api/schemas/micro_affinity_group.py`
- `specs/001-service-skeleton/contracts/micro_affinity_group_processed.schema.json` → `src/adapters/inbound/api/schemas/micro_affinity_group_processed.py`
- `specs/001-service-skeleton/contracts/problem_details.schema.json` → `src/adapters/inbound/api/schemas/problem_details.py`
- `specs/001-service-skeleton/contracts/health_response.schema.json` → `src/adapters/inbound/api/schemas/health_response.py`
- `specs/001-service-skeleton/contracts/json_value.schema.json` → `src/adapters/inbound/api/schemas/json_value.py`

Micro affinity group note:

- `micro_affinity_group.py` is generated from the authoritative JSON Schema and then extended with
	a stable wrapper that rejects duplicate `workload.id` values before the payload reaches the core
	use case.
- For MAG writes, the application-side identity is `micro_ag_id + environment`; `architecture_version`
	remains a required validated field used for application-architecture lookup and is preserved in
	both raw and processed documents.
