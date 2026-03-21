from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends

from src.adapters.inbound.api.dependencies.wiring import get_graph_repository
from src.adapters.inbound.api.schemas.component import Component as ComponentSchema
from src.adapters.inbound.api.schemas.json_value import JsonValue
from src.core.domain.component import Component as DomainComponent
from src.core.ports.graph_repository import GraphRepository
from src.core.use_cases.get_component import GetComponent


router = APIRouter(prefix="/components", tags=["components"])

logger = logging.getLogger("uvicorn.error")


def _to_component_schema(component: DomainComponent) -> ComponentSchema:
    return ComponentSchema(
        component_id=component.component_id,
        name=component.name,
        version=component.version,
        metadata=component.metadata,
    )


@router.post("", response_model=JsonValue)
def echo_components(payload: JsonValue) -> Any:
    serialized_payload = json.dumps(payload.root, ensure_ascii=False)
    is_truncated = len(serialized_payload) > 4096
    logged_payload = serialized_payload[:4096] if is_truncated else serialized_payload

    logger.info(
        "components echo payload_truncated=%s payload=%s",
        is_truncated,
        logged_payload,
    )

    return payload.root


@router.get("/{component_id}", response_model=ComponentSchema)
def get_component(
    component_id: str,
    graph_repository: GraphRepository = Depends(get_graph_repository),
) -> ComponentSchema:
    use_case = GetComponent(graph_repository)
    component = use_case.execute(component_id)
    return _to_component_schema(component)
