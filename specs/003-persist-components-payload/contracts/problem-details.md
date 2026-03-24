# Problem Details Profile

**Branch**: 003-persist-components-payload  
**Date**: 2026-03-21

This project uses RFC 7807 Problem Details as the default error response format.

## Conventions

- `type`: stable URI-like identifier for the problem type (can be `about:blank` for generic cases).
- `title`: short, human-readable summary.
- `status`: HTTP status code.
- `detail`: human-readable details safe for clients (no internal stack traces).

Optional extensions:
- `error_code`: stable machine-readable classification.
- `errors`: structured validation details for 422 responses.

## Example

```json
{
  "type": "https://errors.example.com/validation",
  "title": "Validation error",
  "status": 422,
  "detail": "Request body failed validation.",
  "error_code": "VALIDATION_ERROR",
  "errors": {
    "field": ["must not be empty"]
  }
}
```
