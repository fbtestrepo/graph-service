from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MicroAffinityGroupEdge:
    source_micro_ag_id: str
    destination_micro_ag_id: str

    def sort_key(self) -> tuple[str, str]:
        return (self.source_micro_ag_id, self.destination_micro_ag_id)


def find_path_scoped_cyclic_edges(
    traversal_roots: list[str],
    edges: set[MicroAffinityGroupEdge],
) -> list[MicroAffinityGroupEdge]:
    adjacency: dict[str, list[str]] = {}
    edge_lookup = {edge.sort_key(): edge for edge in edges}

    for edge in sorted(edges, key=lambda edge: edge.sort_key()):
        adjacency.setdefault(edge.source_micro_ag_id, []).append(edge.destination_micro_ag_id)

    visited: set[str] = set()
    active_path_nodes: set[str] = set()
    cyclic_edges: set[MicroAffinityGroupEdge] = set()

    def _visit(node: str) -> None:
        visited.add(node)
        active_path_nodes.add(node)

        for neighbor in adjacency.get(node, []):
            edge = edge_lookup[(node, neighbor)]
            if neighbor in active_path_nodes:
                cyclic_edges.add(edge)
                continue
            if neighbor in visited:
                continue
            _visit(neighbor)

        active_path_nodes.remove(node)

    for root_micro_ag_id in traversal_roots:
        if root_micro_ag_id in visited:
            continue
        _visit(root_micro_ag_id)

    return sorted(cyclic_edges, key=lambda edge: edge.sort_key())


def remove_bypassed_edges(
    edges: set[MicroAffinityGroupEdge],
    bypassed_edges: list[MicroAffinityGroupEdge],
) -> set[MicroAffinityGroupEdge]:
    return set(edges) - set(bypassed_edges)


def build_deployment_steps(
    nodes: set[str],
    edges: set[MicroAffinityGroupEdge],
) -> list[list[str]]:
    remaining_nodes = set(nodes)
    remaining_edges = set(edges)
    steps: list[list[str]] = []

    while remaining_nodes:
        eligible_nodes = sorted(
            node
            for node in remaining_nodes
            if not any(
                edge.source_micro_ag_id == node and edge.destination_micro_ag_id in remaining_nodes
                for edge in remaining_edges
            )
        )
        if not eligible_nodes:
            raise ValueError("Reduced deployment graph still contains a cycle")

        steps.append(eligible_nodes)
        eligible_set = set(eligible_nodes)
        remaining_nodes -= eligible_set
        remaining_edges = {
            edge
            for edge in remaining_edges
            if edge.source_micro_ag_id in remaining_nodes
            and edge.destination_micro_ag_id in remaining_nodes
        }

    return steps

