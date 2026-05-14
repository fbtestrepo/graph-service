# HTTP API Contract: Micro Affinity Group Relationship Enrichment

**Branch**: 008-add-mag-relationships  
**Date**: 2026-05-06

This contract describes the HTTP interface changes for the relationship-enrichment enhancement to
`POST /micro-affinity-groups`.

## Media Types

- Success responses: `application/json`
- Error responses: `application/problem+json` (RFC 7807 Problem Details)

## Standard HTTP Status Mapping

- `400`: Malformed/unparseable JSON request
- `422`: Validation or transformation resolution failure
- `500`: Unhandled infrastructure or transaction failure

## Endpoint

### POST /micro-affinity-groups

Purpose: Persist the raw micro affinity group submission, compute the relationship-enriched
projection, and return the stored processed document.

- Request: `application/json` body conforming to the existing micro affinity group input contract
  (`micro_affinity_group.schema.json`)
- Success responses:
  - `201 Created` when the service creates a new raw/processed record set for the supplied unique
    key
  - `200 OK` when the service overwrites the existing raw/processed record set for the supplied
    unique key
- Response body: the stored processed document conforming to
  `micro_affinity_group_processed.schema.json`
- Transactional side effects on success:
  - persist the raw validated request payload into `micro-affinity-groups`
  - upsert the relationship-enriched projection into `micro-affinity-groups-processed`
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for missing architecture, missing source service,
    unresolved destination service, or other domain transformation failures
  - `500 application/problem+json` if a persistence or transaction failure occurs

## Contract Notes

- The request contract remains closed; `relationships` is not an allowed client-supplied field.
- The response contract adds a required top-level `relationships` list whose entries are generated
  from outgoing architecture relationships.
- Destination workloads may be outside the submitted micro affinity group.
- When a workload has no outgoing relationships, processing continues and no relationship entries
  are emitted for that workload.
- Raw and processed writes must succeed or fail together.