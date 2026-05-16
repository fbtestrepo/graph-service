# Internal Collection Contract: Rename MongoDB Collection Names

**Branch**: 010-rename-collection-names  
**Date**: 2026-05-16

This contract describes the internal persistence naming changes required for MongoDB collection
lookups. It does not change public HTTP routes or payload contracts.

The implementation centralizes these identifiers in
`src/adapters/outbound/mongodb/collection_names.py` and reuses them across the affected
repositories and Mongo-backed persistence tests.

## Contract Scope

- Applies to outbound MongoDB adapters and Mongo-backed persistence tests
- Does not change REST endpoints, response bodies, or request validation contracts
- Does not introduce automatic migration of existing dashed collections

## Required Collection Mappings

| Current Name | New Name | Primary Consumers |
|--------------|----------|-------------------|
| `application-architectures` | `application_architectures` | Application architecture repository, persistence tests, micro affinity group persistence seeding |
| `micro-affinity-groups` | `micro_affinity_groups` | Raw micro affinity group repository and persistence tests |
| `micro-affinity-groups-processed` | `micro_affinity_groups_processed` | Processed micro affinity group repository and persistence tests |

## Collections Explicitly Unchanged

| Name | Reason |
|------|--------|
| `components` | Already compliant with the required naming convention |
| `component_payload_records` | Already compliant with the required naming convention |

## Behavioral Guarantees

- Repository read/write/upsert semantics remain unchanged
- Existing document shapes remain unchanged
- Existing indexes and collection validation behavior remain unchanged
- Transactional raw + processed micro affinity group writes remain unchanged

## Non-Goals

- No dual-read or dual-write support across dashed and underscore names
- No automatic migration of historical data from dashed collections
- No API contract changes