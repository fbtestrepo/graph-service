from __future__ import annotations

from dataclasses import dataclass, field

from src.core.domain.dependency_edge import DependencyEdge
from src.core.use_cases.get_component_dependencies import GetComponentDependencies


@dataclass(slots=True)
class FakeComponentNodeRepository:
    existing_nodes: set[str]
    outgoing_by_source: dict[str, list[DependencyEdge]] = field(default_factory=dict)
    incoming_by_target: dict[str, list[DependencyEdge]] = field(default_factory=dict)

    def upsert(self, node_id: str, payload: dict) -> bool:  # pragma: no cover
        raise NotImplementedError

    def get_by_node_id(self, node_id: str):
        return {"node-id": node_id} if node_id in self.existing_nodes else None

    def get_outgoing_relationship_edges(self, source_node_ids: set[str]) -> list[DependencyEdge]:
        edges: list[DependencyEdge] = []
        for source in source_node_ids:
            edges.extend(self.outgoing_by_source.get(source, []))
        return edges

    def get_incoming_relationship_edges(self, target_node_ids: set[str]) -> list[DependencyEdge]:
        edges: list[DependencyEdge] = []
        for target in target_node_ids:
            edges.extend(self.incoming_by_target.get(target, []))
        return edges


def test_use_case_deduplicates_sorts_and_includes_cycle_edges() -> None:
    # A -> B -> C -> A (cycle)
    # Include duplicates and verify stable ordering + de-dup.
    repo = FakeComponentNodeRepository(
        existing_nodes={"A", "B", "C"},
        outgoing_by_source={
            "A": [
                DependencyEdge("depends-on", "A", "B"),
                DependencyEdge("depends-on", "A", "B"),
            ],
            "B": [DependencyEdge("depends-on", "B", "C")],
            "C": [DependencyEdge("depends-on", "C", "A")],
        },
        incoming_by_target={
            "A": [DependencyEdge("depends-on", "C", "A")],
            "B": [DependencyEdge("depends-on", "A", "B")],
            "C": [DependencyEdge("depends-on", "B", "C")],
        },
    )

    edges = GetComponentDependencies(repo).execute("A")

    assert len(edges) == len(set(edges))
    assert edges == sorted(edges, key=lambda e: e.sort_key())
    assert set(edges) == {
        DependencyEdge("depends-on", "A", "B"),
        DependencyEdge("depends-on", "B", "C"),
        DependencyEdge("depends-on", "C", "A"),
    }


def test_use_case_ignores_non_self_sourced_edges() -> None:
    # The repository might contain relationships where the stored document node-id
    # doesn't match relationship.source.node-id. The use case should ignore such
    # edges by requiring edge.source_node_id to be in the requested frontier.
    repo = FakeComponentNodeRepository(
        existing_nodes={"A"},
        outgoing_by_source={
            "A": [
                DependencyEdge("depends-on", "B", "C"),
                DependencyEdge("depends-on", "A", "C"),
            ]
        },
        incoming_by_target={},
    )

    edges = GetComponentDependencies(repo).execute("A")

    assert edges == [DependencyEdge("depends-on", "A", "C")]


def test_use_case_boundary_rule_includes_in_scope_edges_but_not_hop_21_nodes() -> None:
    # Build a 20-hop chain n0 -> n1 -> ... -> n20.
    # Add an extra edge incident to the boundary node (n20 -> n10) which should be included,
    # and an edge (n20 -> n21) which must be excluded (would introduce a hop-21 node).
    root = "n0"

    outgoing: dict[str, list[DependencyEdge]] = {}
    incoming: dict[str, list[DependencyEdge]] = {}

    for i in range(20):
        src = f"n{i}"
        tgt = f"n{i + 1}"
        edge = DependencyEdge("depends-on", src, tgt)
        outgoing.setdefault(src, []).append(edge)
        incoming.setdefault(tgt, []).append(edge)

    outgoing.setdefault("n20", []).append(DependencyEdge("depends-on", "n20", "n10"))
    outgoing.setdefault("n20", []).append(DependencyEdge("depends-on", "n20", "n21"))

    incoming.setdefault("n10", []).append(DependencyEdge("depends-on", "n20", "n10"))
    incoming.setdefault("n21", []).append(DependencyEdge("depends-on", "n20", "n21"))

    repo = FakeComponentNodeRepository(
        existing_nodes={f"n{i}" for i in range(0, 21)},
        outgoing_by_source=outgoing,
        incoming_by_target=incoming,
    )

    edges = GetComponentDependencies(repo).execute(root)

    assert DependencyEdge("depends-on", "n20", "n10") in edges
    assert DependencyEdge("depends-on", "n20", "n21") not in edges
    assert len(edges) == 21
