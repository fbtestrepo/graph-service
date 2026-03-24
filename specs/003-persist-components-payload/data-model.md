# Data Model: Persist Components Payload

**Branch**: 003-persist-components-payload  
**Date**: 2026-03-21

## Entity: ComponentPayloadRecord

Represents one successful `POST /components` request that was persisted to MongoDB.

### Fields

- **`_id`**: MongoDB ObjectId (database-generated primary key)
- **`received_at`**: UTC timestamp for when the service received the request
- **`payload`**: Any JSON value (object/array/string/number/boolean/null)

### Validation Rules

- `received_at` MUST be present.
- `payload` MUST be present and may be any valid JSON value.

### Relationships

None (this is an append-only audit-style record).

### State / Lifecycle

- Created on successful request handling (before returning `200 OK`).
- No update/delete flows are introduced by this feature.

## Suggested Storage (MongoDB)

- **Database**: `GRAPH_SERVICE_MONGODB_DATABASE`
- **Collection**: `component_payload_records` (exact name is an implementation detail but should be stable)

## Notes

- The persisted record shape is intentionally simple to preserve compatibility with arbitrary JSON root values.
- The system currently does not define retention; retention policy is out of scope for this feature.
