# Problem Details Profile

**Branch**: 004-components-payload-schema  
**Date**: 2026-03-24

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
  "type": "about:blank",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request payload failed validation.",
  "error_code": "validation_failed",
  "errors": {
    "node-id": ["Field required"]
  }
}
```
