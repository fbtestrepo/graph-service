# Problem Details Contract (RFC 7807)

**Branch**: 002-components-echo  
**Date**: 2026-03-19

All non-2xx responses MUST use RFC 7807 Problem Details with media type `application/problem+json`.

## Required Fields

- `type` (string)
- `title` (string)
- `status` (integer)
- `detail` (string)

## Optional Fields

- `error_code` (string)
- `errors` (object of validation error lists)
- additional fields are permitted

## Status Codes Used by This Feature

- `400 Bad Request`: malformed JSON (unparseable request body)
- `422 Unprocessable Entity`: schema/validation errors (e.g., missing required body)
