from __future__ import annotations

from typing import Any

from fastapi import Request


def get_graph_repository(request: Request) -> Any:
    return request.app.state.graph_repository


def get_identity_provider(request: Request) -> Any:
    return request.app.state.identity_provider
