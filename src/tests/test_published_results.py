"""Regression tests pinning results published with Metrinome's papers.

A toolchain upgrade (LLVM, JDK, sympy, ...) or a front-end change must not silently alter them:

- ICSE 2021 (asymptotic path complexity): cyclomatic complexity, NPath complexity, CFG vertex and
  edge counts, and APC of every function in ``experiments/icse_experiment/files`` must equal the
  published reference ``experiments/icse_experiment/data/Unoptimized.csv``. That data was collected
  from C++ builds of an older, differently numbered copy of the files, so rows are matched by
  (demangled) function name only. Only the APC (first element of the published ``apc`` tuple) is
  compared; the second element, the full path-complexity expression, is not a published claim.
- ISSTA 2024 (branching APC with function calls): the ``rfcapc`` result of
  ``FunctionCallPathComplexity`` for every function selected by
  ``tests/cFiles/C-master/CmasterFiles.txt`` (computed as
  ``experiments/function_calls/tests/test_getrgf.py`` does) must equal the ``BranchingAPC`` column of
  ``experiments/branch_apc/data/final_branching_data.csv``.

Expressions are compared numerically at a few values of n, because sympy versions print the same
value differently (``108.0*1.0**n`` vs ``108.000000000000``).
"""
import csv
import math
import re
import tempfile
import unittest
from glob import glob
from os.path import basename, join, splitext
from unittest import mock

import sympy  # type: ignore

from core.env import Env
from core.log import Log
from lang_to_cfg.cpp import CPPConvert
from metric.cyclomatic_complexity import CyclomaticComplexity
from metric.fcn_call_path_complexity import FunctionCallPathComplexity
from metric.npath_complexity import NPathComplexity
from metric.path_complexity import PathComplexity

SAMPLE_POINTS = (1, 7, 30)

ICSE_FILES = "experiments/icse_experiment/files"
ICSE_REFERENCE = "experiments/icse_experiment/data/Unoptimized.csv"
# Functions in ICSE_FILES that have no row in the published data.
ICSE_UNPUBLISHED = {"motion"}  # 25_pos_vel_acc.c

ISSTA_BENCHMARK = "tests/cFiles/C-master/CmasterFiles.txt"
ISSTA_REFERENCE = "experiments/branch_apc/data/final_branching_data.csv"

_TMP_PATCHES: list = []


def setUpModule() -> None:  # pylint: disable=invalid-name
    """Run the converters in a private temp dir, so tracked dirs and concurrent runs are untouched."""
    root = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
    _TMP_PATCHES.extend([mock.patch.object(Env, "TMP_PATH", join(root.name, "tmp")),
                         mock.patch.object(Env, "TMP_DOT_PATH", join(root.name, "tmp_dot"))])
    for patch in _TMP_PATCHES:
        patch.start()
    _TMP_PATCHES.append(root)


def tearDownModule() -> None:  # pylint: disable=invalid-name
    """Restore Env's temp paths and delete the private temp dir."""
    root = _TMP_PATCHES.pop()
    for patch in _TMP_PATCHES:
        patch.stop()
    _TMP_PATCHES.clear()
    root.cleanup()


def evaluate_at(expression, n_value: int) -> float:
    """Evaluate a printed or sympy expression of n at n = `n_value`."""
    expr = sympy.sympify(str(expression))
    names = {symbol.name for symbol in expr.free_symbols}
    if not names <= {"n"}:
        raise ValueError(f"unexpected symbols {names} in {expression}")
    return float(expr.subs({symbol: n_value for symbol in expr.free_symbols}))


def assert_same_function_of_n(test: unittest.TestCase, actual, expected) -> None:
    """Assert two expressions of n agree at SAMPLE_POINTS within a relative tolerance of 1e-9."""
    for n_value in SAMPLE_POINTS:
        got, want = evaluate_at(actual, n_value), evaluate_at(expected, n_value)
        test.assertTrue(math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-12),
                        f"{actual} != {expected} at n={n_value} ({got} vs {want})")


def published_function_name(graph_name: str) -> str:
    """Function name of a published graph name: `04_prime_cfg._Z11check_primei` -> `check_prime`."""
    function = graph_name.split(".", 1)[1]
    if mangled := re.fullmatch(r"_Z(\d+)(\w+)", function):
        return mangled.group(2)[:int(mangled.group(1))]
    return function


def published_apc(apc_tuple: str) -> str:
    """APC (first element) of a published `(apc, path complexity)` tuple string."""
    match = re.fullmatch(r"\(\s*'?([^,']+)'?\s*,.*\)", apc_tuple)
    if match is None:
        raise ValueError(f"cannot parse published apc {apc_tuple!r}")
    return match.group(1)


def read_reference(path: str) -> list[dict[str, str]]:
    """Rows of a published CSV."""
    with open(Env.project_file(path), newline="") as reference:
        return list(csv.DictReader(reference))


class TestICSE2021(unittest.TestCase):
    """Metrics of the ICSE 2021 benchmark match the published, unoptimized-build data."""

    @classmethod
    def setUpClass(cls) -> None:
        """Convert every benchmark file; index the graphs by function name."""
        converter = CPPConvert(Log(display_output=False))
        cls.graphs = {}
        cls.files = sorted(glob(join(Env.project_file(ICSE_FILES), "*.c")))
        for source in cls.files:
            graphs = converter.to_graph(splitext(source)[0], ".c") or {}
            for graph in graphs.values():
                function = graph.name.split(".", 1)[1]
                assert function not in cls.graphs, f"duplicate function {function}"
                cls.graphs[function] = graph
        cls.published = read_reference(ICSE_REFERENCE)

    def test_every_file_converts(self) -> None:
        """Each benchmark file yields at least one CFG."""
        converted = {basename(graph.name.split(".", 1)[0]).rstrip("_") for graph in self.graphs.values()}
        self.assertEqual({splitext(basename(source))[0] for source in self.files}, converted)

    def test_functions_match_published_rows(self) -> None:
        """Every published row has a function, and only known functions lack a published row."""
        self.assertEqual(31, len(self.published))
        published = {published_function_name(row["graph_name"]) for row in self.published}
        self.assertEqual(set(), published - set(self.graphs))
        self.assertEqual(ICSE_UNPUBLISHED, set(self.graphs) - published)

    def test_metrics_match_published(self) -> None:
        """Cyclomatic, NPath, vertex count, edge count, and APC equal the published values."""
        log = Log(display_output=False)
        cyclomatic, npath, path = CyclomaticComplexity(log), NPathComplexity(log), PathComplexity(log)
        for row in self.published:
            function = published_function_name(row["graph_name"])
            with self.subTest(function=function, published=row["graph_name"]):
                graph = self.graphs[function]
                self.assertEqual(float(row["cyclo"]), cyclomatic.evaluate(graph))
                self.assertEqual(float(row["npath"]), npath.evaluate(graph))
                self.assertEqual(float(row["vertex_count"]), graph.graph.num_vertices)
                self.assertEqual(float(row["edge_count"]), graph.graph.edge_count())
                assert_same_function_of_n(self, path.evaluate(graph)[0], published_apc(row["apc"]))


def issta_benchmark() -> list[tuple[str, list[str]]]:
    """(source file, function filters) per line of the ISSTA benchmark list, as test_getrgf.py reads it."""
    with open(Env.project_file(ISSTA_BENCHMARK)) as listing:
        lines = [line.rstrip() for line in listing]
    return [(Env.project_file(line.split()[0]), line.split()[1:]) for line in lines if line[:1] != "*"]


def is_selected(graph_name: str, filters: list[str]) -> bool:
    """test_getrgf.py's selection: no filter, or a filter that is a substring of the function name."""
    function = graph_name.split(".")[1]
    return not filters or any(name in function for name in filters)


class TestISSTA2024(unittest.TestCase):
    """Branching APC of the ISSTA 2024 C-master benchmark matches the published data."""

    @classmethod
    def setUpClass(cls) -> None:
        """Convert every benchmark file and select the functions test_getrgf.py analyses."""
        converter = CPPConvert(Log(display_output=False))
        cls.selected = []  # (graph, all graphs of its file)
        for source, filters in issta_benchmark():
            graphs = converter.to_graph(splitext(source)[0], ".c")
            assert graphs, f"{source} did not convert"
            cls.selected += [(graph, graphs) for name, graph in graphs.items() if is_selected(name, filters)]
        cls.published = {row["graph_name"]: row["BranchingAPC"] for row in read_reference(ISSTA_REFERENCE)}

    def test_selection_matches_published_rows(self) -> None:
        """The benchmark selects exactly the 79 published functions."""
        names = [graph.name for graph, _ in self.selected]
        self.assertEqual(79, len(self.published))
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(self.published), set(names))

    def test_branching_apc_matches_published(self) -> None:
        """FunctionCallPathComplexity's rfcapc equals the published BranchingAPC."""
        computer = FunctionCallPathComplexity(Log(display_output=False))
        for graph, graphs in self.selected:
            with self.subTest(function=graph.name):
                self.assertIn(graph.name, self.published)
                result = computer.evaluate(graph, graphs)
                assert_same_function_of_n(self, result["rfcapc"], self.published[graph.name])


if __name__ == "__main__":
    unittest.main()
