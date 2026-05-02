# CALM v1.2 Schemas

This directory contains the pinned, local meta-schemas for the **FINOS Common Architecture Language Model (CALM)** Version 1.2 

These local files act as the single source of truth for generating our Pydantic data models

## Download Source

To mirror these files locally from the official FINOS release, run the following commands from the root of the repository:

```bash
# Ensure the directory exists
mkdir -p schemas/calm/v1_2

cd schemas/calm/v1_2

curl -L https://calm.finos.org/release/1.2/meta/calm.json -o calm.json
curl -L https://calm.finos.org/release/1.2/meta/core.json -o core.json
curl -L https://calm.finos.org/release/1.2/meta/control.json -o control.json
curl -L https://calm.finos.org/release/1.2/meta/flow.json -o flow.json
curl -L https://calm.finos.org/release/1.2/meta/interface.json -o interface.json
