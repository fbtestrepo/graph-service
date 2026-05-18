from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MicroAffinityGroupEdge:
    source_micro_ag_id: str
    destination_micro_ag_id: str

    def sort_key(self) -> tuple[str, str]:
        return (self.source_micro_ag_id, self.destination_micro_ag_id)


def reduce_cyclic_edges(
    edges: set[MicroAffinityGroupEdge],
) -> tuple[set[MicroAffinityGroupEdge], list[MicroAffinityGroupEdge]]:
    remaining_edges = set(edges)
    bypassed_edges: list[MicroAffinityGroupEdge] = []

    while True:
        cycle_edges = _find_cycle_edges(remaining_edges)
        if not cycle_edges:
            break

        edge_to_bypass = min(cycle_edges, key=lambda edge: edge.sort_key())
        remaining_edges.remove(edge_to_bypass)
        bypassed_edges.append(edge_to_bypass)

    return remaining_edges, sorted(bypassed_edges, key=lambda edge: edge.sort_key())


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


def _find_cycle_edges(edges: set[MicroAffinityGroupEdge]) -> set[MicroAffinityGroupEdge]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    for edge in edges:
        adjacency[edge.source_micro_ag_id].add(edge.destination_micro_ag_id)
        nodes.add(edge.source_micro_ag_id)
        nodes.add(edge.destination_micro_ag_id)

    strongly_connected_components = _tarjan_strongly_connected_components(nodes, adjacency)
    cycle_edges: set[MicroAffinityGroupEdge] = set()

    for component in strongly_connected_components:
        if len(component) > 1:
            cycle_edges |= {
                edge
                for edge in edges
                if edge.source_micro_ag_id in component and edge.destination_micro_ag_id in component
            }
            continue

        node = next(iter(component))
        self_edge = MicroAffinityGroupEdge(node, node)
        if self_edge in edges:
            cycle_edges.add(self_edge)

    return cycle_edges


def _tarjan_strongly_connected_components(
    nodes: set[str],
    adjacency: dict[str, set[str]],
) -> list[set[str]]:
    index = 0
    stack: list[str] = []
    stack_members: set[str] = set()
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    components: list[set[str]] = []

    def _strongconnect(node: str) -> None:
        nonlocal index

        indexes[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        stack_members.add(node)

        for neighbor in sorted(adjacency.get(node, ())):
            if neighbor not in indexes:
                _strongconnect(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in stack_members:
                lowlinks[node] = min(lowlinks[node], indexes[neighbor])

        if lowlinks[node] != indexes[node]:
            return

        component: set[str] = set()
        while stack:
            member = stack.pop()
            stack_members.remove(member)
            component.add(member)
            if member == node:
                break
        components.append(component)

    for node in sorted(nodes):
        if node not in indexes:
            _strongconnect(node)

    return components