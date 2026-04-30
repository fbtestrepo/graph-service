from __future__ import annotations

from dataclasses import dataclass

from src.core.domain.dependency_edge import DependencyEdge
from src.core.exceptions.component_not_found import ComponentNotFound
from src.core.ports.component_node_repository import ComponentNodeRepository


_MAX_HOPS = 20


@dataclass(frozen=True, slots=True)
class GetComponentDependencies:
    component_node_repository: ComponentNodeRepository

    def execute(self, node_id: str) -> list[DependencyEdge]:
        payload = self.component_node_repository.get_by_node_id(node_id)
        if payload is None:
            raise ComponentNotFound(node_id)

        downstream_edges, downstream_depths = self._traverse_downstream(node_id)
        upstream_edges, upstream_depths = self._traverse_upstream(node_id)

        in_scope_nodes = set(downstream_depths.keys()) | set(upstream_depths.keys())

        boundary_nodes = {
            n for n, d in downstream_depths.items() if d == _MAX_HOPS
        } | {n for n, d in upstream_depths.items() if d == _MAX_HOPS}

        boundary_edges: set[DependencyEdge] = set()
        if boundary_nodes:
            boundary_edges |= {
                e
                for e in self.component_node_repository.get_outgoing_relationship_edges(
                    boundary_nodes
                )
                if e.source_node_id in boundary_nodes
            }
            boundary_edges |= {
                e
                for e in self.component_node_repository.get_incoming_relationship_edges(
                    boundary_nodes
                )
                if e.target_node_id in boundary_nodes
            }
            boundary_edges = {
                e
                for e in boundary_edges
                if e.source_node_id in in_scope_nodes and e.target_node_id in in_scope_nodes
            }

        all_edges = downstream_edges | upstream_edges | boundary_edges
        return sorted(all_edges, key=lambda e: e.sort_key())

    def _traverse_downstream(self, root_node_id: str) -> tuple[set[DependencyEdge], dict[str, int]]:
        edges: set[DependencyEdge] = set()
        depths: dict[str, int] = {root_node_id: 0}

        frontier: set[str] = {root_node_id}
        for depth in range(_MAX_HOPS):
            if not frontier:
                break

            outgoing = self.component_node_repository.get_outgoing_relationship_edges(frontier)
            next_frontier: set[str] = set()
            for edge in outgoing:
                if edge.source_node_id not in frontier:
                    continue
                edges.add(edge)

                if edge.target_node_id not in depths:
                    depths[edge.target_node_id] = depth + 1
                    next_frontier.add(edge.target_node_id)

            frontier = next_frontier

        return edges, depths

    def _traverse_upstream(self, root_node_id: str) -> tuple[set[DependencyEdge], dict[str, int]]:
        edges: set[DependencyEdge] = set()
        depths: dict[str, int] = {root_node_id: 0}

        frontier: set[str] = {root_node_id}
        for depth in range(_MAX_HOPS):
            if not frontier:
                break

            incoming = self.component_node_repository.get_incoming_relationship_edges(frontier)
            next_frontier: set[str] = set()
            for edge in incoming:
                if edge.target_node_id not in frontier:
                    continue
                edges.add(edge)

                if edge.source_node_id not in depths:
                    depths[edge.source_node_id] = depth + 1
                    next_frontier.add(edge.source_node_id)

            frontier = next_frontier

        return edges, depths
