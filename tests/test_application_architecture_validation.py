from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.adapters.inbound.api.schemas.application_architecture import ApplicationArchitecture


def _valid_payload() -> dict:
    return {
        "metadata": {
            "AssetID": "Asset123",
            "version": "1.0.0",
            "created": "2026-05-02",
        },
        "nodes": [],
        "relationships": [],
    }


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(lambda p: {k: v for k, v in p.items() if k != "metadata"}, id="missing-metadata"),
        pytest.param(lambda p: {**p, "metadata": []}, id="non-object-metadata"),
        pytest.param(lambda p: {**p, "metadata": {**p["metadata"], "AssetID": "Asset-123"}}, id="invalid-asset-id"),
        pytest.param(lambda p: {**p, "metadata": {**p["metadata"], "version": "1.0"}}, id="invalid-version"),
        pytest.param(lambda p: {**p, "metadata": {**p["metadata"], "created": "2026-02-30"}}, id="invalid-created"),
    ],
)
def test_application_architecture_validation_rejects_invalid_metadata(payload) -> None:
    with pytest.raises(ValidationError):
        ApplicationArchitecture.model_validate(payload(_valid_payload()))
