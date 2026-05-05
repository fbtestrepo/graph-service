# HTTP API Contract (Working Copy)

**Branch**: 006-calm-architecture-ingest  
**Date**: 2026-05-02

This contract document describes the HTTP interface relevant to the CALM architecture ingestion
feature.

## Media Types

- Success responses: `application/json`
- Error responses: `application/problem+json` (RFC 7807 Problem Details)

## Standard HTTP Status Mapping

- `400`: Malformed/unparseable JSON request
- `422`: Validation error (CALM schema or metadata constraints)
- `500`: Unhandled infrastructure failure (no stack trace leaked)

## Endpoints

### POST /application-architectures

Purpose: Validate and upsert a CALM application architecture document keyed by
`metadata.AssetID` + `metadata.version`.

- Request: `application/json` body conforming to `application_architecture.schema.json`
- Success responses:
  - `201 Created` when the service creates a new record for the supplied `AssetID` and `version`
  - `200 OK` when the service overwrites an existing record for the supplied `AssetID` and
    `version`
- Response body: the stored application architecture document
- Side effect (on success): the service persists the payload into MongoDB collection
  `application-architectures`
- Error responses:
  - `400 application/problem+json` for malformed/unparseable JSON
  - `422 application/problem+json` for CALM schema or metadata validation failures
  - `500 application/problem+json` if persistence fails for any reason

## Contract Notes

- The canonical CALM contract entry point remains `schemas/calm/v1_2/calm.json`.
- The authoritative service contract used for code generation lives under
  `specs/001-service-skeleton/contracts/`.
- `application_architecture.schema.json` is the feature-local service contract wrapper that makes
  root `metadata` mandatory and constrains `AssetID`, `version`, and `created`.
- The endpoint distinguishes create vs overwrite using HTTP status codes rather than an extra
  response flag.