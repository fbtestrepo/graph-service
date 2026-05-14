from __future__ import annotations

from typing import Any

from fastapi import Request


def get_graph_repository(request: Request) -> Any:
    return request.app.state.graph_repository


def get_identity_provider(request: Request) -> Any:
    return request.app.state.identity_provider


def get_component_payload_repository(request: Request) -> Any:
    return request.app.state.component_payload_repository


def get_component_node_repository(request: Request) -> Any:
    return request.app.state.component_node_repository


def get_application_architecture_repository(request: Request) -> Any:
    return request.app.state.application_architecture_repository


def get_micro_affinity_group_repository(request: Request) -> Any:
    return request.app.state.micro_affinity_group_repository


def get_micro_affinity_group_processed_repository(request: Request) -> Any:
    return request.app.state.micro_affinity_group_processed_repository


def get_transaction_manager(request: Request) -> Any:
    return request.app.state.transaction_manager
