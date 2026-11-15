"""Count the paths through a CFG up to a given execution length.

Path complexity describes how the number of START-to-EXIT paths of length at most n grows with n;
this metric reports that number exactly for one concrete bound, using the same notion of length
(one step per CFG edge) as the base cases from which the path complexity is fitted.
"""
from collections import defaultdict
from typing import List

from core.log import Log
from graph.control_flow_graph import ControlFlowGraph
from graph.graph import Graph
from metric import metric

DEFAULT_PATH_LENGTH = 50


def count_paths(graph: Graph, max_length: int) -> int:
    """Return the number of START-to-EXIT paths with at most `max_length` edges (exact)."""
    adjacency = graph.adjacency_list()
    paths_ending_at: dict[int, int] = {graph.start_node: 1}
    total = 1 if graph.start_node == graph.end_node else 0
    for _ in range(max_length):
        extended: defaultdict[int, int] = defaultdict(int)
        for node, count in paths_ending_at.items():
            for successor in adjacency[node]:
                extended[successor] += count
        paths_ending_at = extended
        total += paths_ending_at.get(graph.end_node, 0)
    return total


class BoundedPathCount(metric.MetricAbstract):
    """Number of paths through a CFG whose length is at most a fixed bound."""

    def __init__(self, logger: Log, max_length: int = DEFAULT_PATH_LENGTH) -> None:
        """Count paths of at most `max_length` edges."""
        if max_length < 0:
            raise ValueError("max_length must be non-negative")
        self.logger = logger
        self.max_length = max_length

    def name(self) -> str:
        """Get the name of the metric."""
        return "Bounded Path Count"

    def evaluate(self, cfg: ControlFlowGraph, all_cfgs: List[ControlFlowGraph] = []) -> int:
        """Return the number of START-to-EXIT paths in `cfg` with at most `max_length` edges."""
        return count_paths(cfg.graph, self.max_length)
