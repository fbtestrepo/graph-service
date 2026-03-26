from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from src.adapters.inbound.api.dependencies.wiring import get_component_node_repository
from src.adapters.inbound.api.schemas.component_node import ComponentNode
from src.core.ports.component_node_repository import ComponentNodeRepository
from src.core.use_cases.get_component_node import GetComponentNode
from src.core.use_cases.upsert_component_node import UpsertComponentNode


router = APIRouter(prefix="/components", tags=["components"])


@router.post("", response_model=ComponentNode, response_model_exclude_none=True)
def upsert_component_node(
    payload: ComponentNode,
    response: Response,
    component_node_repository: ComponentNodeRepository = Depends(get_component_node_repository),
) -> ComponentNode:
    use_case = UpsertComponentNode(component_node_repository)
    result = use_case.execute(payload.model_dump(by_alias=True, exclude_none=True))
    response.status_code = status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    return payload


@router.get("/{component_id}", response_model=ComponentNode, response_model_exclude_none=True)
def get_component_node(
    component_id: str,
    component_node_repository: ComponentNodeRepository = Depends(get_component_node_repository),
) -> ComponentNode:
    use_case = GetComponentNode(component_node_repository)
    payload = use_case.execute(component_id)
    return ComponentNode.model_validate(payload)
