from __future__ import annotations

from fastapi import APIRouter, Depends

from src.adapters.inbound.api.dependencies.wiring import get_graph_repository
from src.adapters.inbound.api.schemas.component import Component as ComponentSchema
from src.core.domain.component import Component as DomainComponent
from src.core.ports.graph_repository import GraphRepository
from src.core.use_cases.get_component import GetComponent


router = APIRouter(prefix="/components", tags=["components"])


def _to_component_schema(component: DomainComponent) -> ComponentSchema:
    return ComponentSchema(
        component_id=component.component_id,
        name=component.name,
        version=component.version,
        metadata=component.metadata,
    )


@router.get("/{component_id}", response_model=ComponentSchema)
def get_component(
    component_id: str,
    graph_repository: GraphRepository = Depends(get_graph_repository),
) -> ComponentSchema:
    use_case = GetComponent(graph_repository)
    component = use_case.execute(component_id)
    return _to_component_schema(component)
