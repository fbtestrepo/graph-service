# Quickstart: Components Echo Endpoint

**Branch**: 002-components-echo  
**Date**: 2026-03-19

This quickstart verifies the new `POST /components` echo endpoint.

## Prerequisites

- Python 3.12+

## Install

```bash
cd /Users/ertant/work/vscode-projects/graph-service

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e '.[dev]'
```

## Run (development)

```bash
cd /Users/ertant/work/vscode-projects/graph-service
uvicorn src.infrastructure.main:create_app --factory --reload --port 8000
```

## Verify

### Echo object JSON

```bash
curl -sS -X POST http://localhost:8000/components \
  -H 'content-type: application/json' \
  -d '{"hello": "world", "n": 123}'
```

Expected:
- `200 OK`
- response body equals the request JSON
- server logs include the payload (truncated to first 4096 characters with truncation indicated if needed)

### Echo array JSON

```bash
curl -sS -X POST http://localhost:8000/components \
  -H 'content-type: application/json' \
  -d '[1, 2, 3, {"x": true}]'
```

Expected: `200 OK` with identical JSON in the response.

### Malformed JSON → 400 Problem Details

```bash
curl -sS -X POST http://localhost:8000/components \
  -H 'content-type: application/json' \
  -d '{"broken": '
```

Expected:
- `400`
- `content-type: application/problem+json`
- a problem-details body indicating malformed JSON
