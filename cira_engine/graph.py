"""
CiRA-inspired Cause-Effect Graph (CEG) Constructor.
Translates a LabeledSentence into a directed graph of cause → effect nodes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from .labeler import LabeledSentence, Event


@dataclass
class CEGNode:
    node_id: str
    label: str
    node_type: str          # "cause" | "effect" | "intermediate" | "negated_cause" | "precondition"
    negated: bool = False


@dataclass
class CEGEdge:
    source_id: str
    target_id: str
    edge_type: str          # "AND" | "OR" | "direct"


@dataclass
class CauseEffectGraph:
    nodes: Dict[str, CEGNode] = field(default_factory=dict)
    edges: List[CEGEdge] = field(default_factory=list)
    cause_ids: List[str] = field(default_factory=list)
    effect_ids: List[str] = field(default_factory=list)
    connector_type: str = ""

    def add_node(self, node: CEGNode):
        self.nodes[node.node_id] = node

    def add_edge(self, edge: CEGEdge):
        self.edges.append(edge)


def _safe_id(text: str, prefix: str, counter: List[int]) -> str:
    counter[0] += 1
    return f"{prefix}_{counter[0]}"


def _build_subtree(
    event: Event,
    graph: CauseEffectGraph,
    prefix: str,
    counter: List[int],
    parent_id: Optional[str] = None,
    parent_edge_type: str = "direct",
) -> str:
    """Recursively build nodes/edges for an Event tree. Returns the root node id."""

    node_id = _safe_id(event.text, prefix, counter)
    node = CEGNode(
        node_id=node_id,
        label=event.text[:120],      # truncate for display
        node_type=event.event_type,
        negated=event.negated,
    )
    graph.add_node(node)

    if parent_id:
        graph.add_edge(CEGEdge(parent_id, node_id, parent_edge_type))

    if event.sub_events:
        for child_event in event.sub_events:
            _build_subtree(child_event, graph, prefix, counter,
                           parent_id=node_id, parent_edge_type=event.connector or "AND")

    return node_id


class CEGBuilder:
    """CiRA Step 3: Build a Cause-Effect Graph from a LabeledSentence."""

    def build(self, labeled: LabeledSentence) -> CauseEffectGraph:
        graph = CauseEffectGraph(connector_type=labeled.connector_type)
        counter = [0]

        # ── Causes ────────────────────────────────────────────────────────────
        cause_root_ids = []
        for event in labeled.causes:
            nid = _build_subtree(event, graph, "C", counter)
            cause_root_ids.append(nid)
            graph.cause_ids.append(nid)

        # If multiple top-level causes, infer AND / OR from connector text
        if len(cause_root_ids) > 1:
            # Create an intermediate gate node
            gate_id = f"GATE_{counter[0]+1}"
            counter[0] += 1
            gate = CEGNode(gate_id, "AND-gate", "intermediate")
            graph.add_node(gate)
            for cid in cause_root_ids:
                graph.add_edge(CEGEdge(cid, gate_id, "AND"))
            cause_root_ids = [gate_id]

        # ── Effects ───────────────────────────────────────────────────────────
        for event in labeled.effects:
            nid = _build_subtree(event, graph, "E", counter)
            graph.effect_ids.append(nid)
            for cid in cause_root_ids:
                graph.add_edge(CEGEdge(cid, nid, "direct"))

        return graph

    def get_leaf_causes(self, graph: CauseEffectGraph) -> List[CEGNode]:
        """Return leaf-level cause nodes (the actual test variables)."""
        non_leaf_sources = {e.source_id for e in graph.edges}
        # Leaf = node that is never a source AND is a cause/negated_cause/precondition
        leaves = []
        for nid, node in graph.nodes.items():
            if node.node_type in ("cause", "negated_cause", "precondition", "context"):
                if nid not in non_leaf_sources or not graph.edges:
                    leaves.append(node)
        return leaves if leaves else [graph.nodes[nid] for nid in graph.cause_ids if nid in graph.nodes]
