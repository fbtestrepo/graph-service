# Data Model: Components Echo Endpoint

**Branch**: 002-components-echo  
**Date**: 2026-03-19

## Overview

This feature does not introduce new domain entities, persistence models, or state transitions.

## Data Types

### JSON Value (request/response)

- **Name**: JSON value (free-form)
- **Allowed shapes**: object, array, string, number, boolean, null
- **Validation rule**: request body must be valid JSON; malformed JSON is rejected with `400` Problem Details.

## Relationships

None.
