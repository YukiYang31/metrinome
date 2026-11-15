"""Tests for the bounded path count metric (paths of length <= k)."""
import unittest

from core.env import Env
from core.log import Log
from graph.graph import EdgeListGraph
from lang_to_cfg.cpp import CPPConvert
from metric.bounded_paths import BoundedPathCount, count_paths
from metric.path_complexity import BaseCaseBFS


def brute_force_paths(edges: list[list[int]], num_vertices: int, max_length: int) -> int:
    """Enumerate every START-to-EXIT walk of at most `max_length` edges one by one."""
    successors: dict[int, list[int]] = {node: [] for node in range(num_vertices)}
    for source, target in edges:
        successors[source].append(target)

    def walks_from(node: int, budget: int) -> int:
        found = 1 if node == num_vertices - 1 else 0
        if budget == 0:
            return found
        return found + sum(walks_from(nxt, budget - 1) for nxt in successors[node])

    return walks_from(0, max_length)


# START = 0, EXIT = last node.
GRAPHS = {
    "straight line": ([[0, 1], [1, 2]], 3),
    "if/else": ([[0, 1], [0, 2], [1, 3], [2, 3]], 4),
    "while loop": ([[0, 1], [1, 2], [2, 1], [1, 3]], 4),
    "loop with if/else body": ([[0, 1], [1, 2], [1, 3], [2, 4], [3, 4], [4, 1], [1, 5]], 6),
    "nested loops": ([[0, 1], [1, 2], [2, 3], [3, 2], [2, 4], [4, 1], [1, 5]], 6),
}


class TestBoundedPathCount(unittest.TestCase):
    """The metric counts exactly the START-to-EXIT paths of bounded length."""

    def test_matches_enumeration(self) -> None:
        """Counts agree with explicit enumeration of all walks, for every bound."""
        for name, (edges, num_vertices) in GRAPHS.items():
            graph = EdgeListGraph(edges, num_vertices)
            for max_length in range(12):
                with self.subTest(graph=name, max_length=max_length):
                    self.assertEqual(brute_force_paths(edges, num_vertices, max_length),
                                     count_paths(graph, max_length))

    def test_hand_counted_values(self) -> None:
        """A while loop adds one path per two extra steps; an if/else body doubles them per iteration."""
        loop = EdgeListGraph(*GRAPHS["while loop"])
        self.assertEqual([0, 0, 1, 1, 2, 2, 3], [count_paths(loop, k) for k in range(7)])
        branchy_loop = EdgeListGraph(*GRAPHS["loop with if/else body"])
        # Exit after 0, 1, 2 iterations of a 3-edge loop with 2 bodies: 1 + 2 + 4 paths by length 8.
        self.assertEqual(7, count_paths(branchy_loop, 8))

    def test_agrees_with_path_complexity_base_cases(self) -> None:
        """The metric is the quantity APC is fitted to: the exact path counts of the BFS base cases."""
        source = Env.project_file("experiments/icse_experiment/files/14_euclid_GCD")
        graphs = CPPConvert(Log(display_output=False)).to_graph(source, ".c")
        self.assertIsNotNone(graphs)
        graph = next(cfg.graph for name, cfg in graphs.items() if name.endswith(".gcd.dot"))
        base_cases, _ = BaseCaseBFS(Log(display_output=False)).get(graph, None, None, 0, 40)
        self.assertEqual([int(count) for count in base_cases],
                         [count_paths(graph, k) for k in range(40)])

    def test_metric_uses_configured_bound(self) -> None:
        """BoundedPathCount evaluates count_paths at its configured length and rejects negative bounds."""
        graph = EdgeListGraph(*GRAPHS["while loop"])

        class FakeCfg:  # pylint: disable=too-few-public-methods
            """Minimal stand-in exposing the `graph` attribute the metric reads."""

            def __init__(self, inner: EdgeListGraph) -> None:
                self.graph = inner

        self.assertEqual(3, BoundedPathCount(Log(display_output=False), 6).evaluate(FakeCfg(graph)))
        with self.assertRaises(ValueError):
            BoundedPathCount(Log(display_output=False), -1)


if __name__ == "__main__":
    unittest.main()
