"""Front-end correctness and cross-front-end consistency tests.

Fixtures live in ``tests/fixtures``. The cross-front-end tests convert equivalent C (clang -O0 + opt
dot-cfg) and Java (javac + bytecode CFG extractor) functions and require the same cyclomatic
complexity, NPath complexity, and APC growth class (constant, polynomial of degree d, exponential),
each also checked against a hand derivation. Vertex/edge counts and exact APC expressions are not
compared: the representations differ in ways APC is sensitive to (javac puts loop conditions at the
bottom, so the nested-loop cycle is shorter: C ``1.1939**n`` vs Java ``1.272**n``).

Known divergences, deliberately not asserted:

- ``&&``/``||`` in a loop condition: clang -O0 materializes the condition's value with a phi in a
  join block and branches on it, adding a path that Java's short-circuit jumps lack.
  ``while (i < n && a[i] != x) i++;`` gives NPath 4 and APC ``1.2207**n`` in C, NPath 3 and APC ``n``
  in Java (cyclomatic 3 in both). In an ``if`` condition both front-ends short-circuit and agree.
- Ternary with constant arms: clang -O0 emits ``select`` for ``x > 0 ? 1 : 2`` (no branch, cyclomatic
  1) while javac branches (cyclomatic 2). Ternaries with a non-constant arm branch in both and agree.
- Java ``switch`` on a String: javac lowers it to a ``hashCode`` switch, ``equals`` tests, and an index
  switch (3 cases: cyclomatic 7, NPath 15); C has no counterpart.
"""
import os
import subprocess
import tempfile
import unittest
from os.path import basename, join
from unittest import mock

import sympy  # type: ignore

from core.env import Env, ToolNotFoundError
from core.log import Log
from lang_to_cfg.cpp import CPPConvert
from lang_to_cfg.java import JavaConvert
from metric.cyclomatic_complexity import CyclomaticComplexity
from metric.npath_complexity import NPathComplexity
from metric.path_complexity import PathComplexity

FIXTURES = "tests/fixtures"
LOG = Log(display_output=False)

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


def fixture(name: str) -> str:
    """Absolute path of a fixture, without its extension."""
    return Env.project_file(join(FIXTURES, name))


def convert_c(path: str) -> dict:
    """CFGs of a C file (path without extension), keyed by function name."""
    graphs = CPPConvert(LOG).to_graph(path, ".c")
    assert graphs, f"{path}.c did not convert"
    return {graph.name.split(".", 1)[1]: graph for graph in graphs.values()}


def convert_java(path: str) -> dict:
    """CFGs of a Java file (path without extension), keyed by `<Class>_<method>` (`Outer$1_method`)."""
    graphs = JavaConvert(LOG).to_graph(path, ".java")
    assert graphs, f"{path}.java did not convert"
    return {basename(dot).removesuffix("_0_basic.dot"): graph for dot, graph in graphs.items()}


def growth_class(apc) -> str:
    """Asymptotic class of an APC: constant, polynomial of degree d, or exponential."""
    expr = sympy.sympify(str(apc))
    if not expr.free_symbols:
        return "constant"
    if expr.is_polynomial(*expr.free_symbols):
        return f"polynomial of degree {sympy.degree(expr)}"
    return "exponential"


class TestCSwitch(unittest.TestCase):
    """Switches with three or more successors keep every edge (LLVM record ports :s0, :s1, ...)."""

    def test_four_way_switch(self) -> None:
        """
        Blocks at -O0, in order: 0 entry (switch), 1-4 the four cases, 5 default, 6 epilogue (return).

        The switch block reaches the four cases and the default; each of them falls into the epilogue.
        Reading `Node:s2 -> X` as an edge from node 2 would add (2, X) and drop (0, X).
        """
        graph = convert_c(fixture("switch4"))["classify"]
        edges = sorted(tuple(edge) for edge in graph.graph.edge_rules())
        self.assertEqual(7, graph.graph.num_vertices)
        self.assertEqual([(0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
                          (1, 6), (2, 6), (3, 6), (4, 6), (5, 6)], edges)
        # A switch-only function has one independent path per case plus the default.
        self.assertEqual(4 + 1, CyclomaticComplexity(LOG).evaluate(graph))


class TestLegacyC(unittest.TestCase):
    """C that clang 14 accepted with warnings still converts on clang >= 16, where it is an error."""

    def test_fixture_triggers_legacy_diagnostics(self) -> None:
        """The fixture really uses an implicit declaration and an incompatible function pointer."""
        compiled = subprocess.run([Env.clang(), "-fsyntax-only", fixture("legacy") + ".c"],
                                  capture_output=True, text=True, check=False)
        self.assertIn("implicit-function-declaration", compiled.stderr)
        self.assertIn("incompatible-function-pointer-types", compiled.stderr)

    def test_legacy_c_converts(self) -> None:
        """Every function gets a CFG; helper's while loop gives cyclomatic complexity 2."""
        graphs = convert_c(fixture("legacy"))
        self.assertEqual({"by_value", "sort_and_count", "helper"}, set(graphs))
        for name, graph in graphs.items():
            with self.subTest(function=name):
                self.assertGreater(graph.graph.edge_count(), 0)
        self.assertEqual(2, CyclomaticComplexity(LOG).evaluate(graphs["helper"]))


class TestJavaNestedClasses(unittest.TestCase):
    """Methods of anonymous and nested classes are analysed along with the outer class."""

    def test_anonymous_class_methods(self) -> None:
        """FileSystemUtils' anonymous SimpleFileVisitor ($1) methods get CFGs."""
        graphs = convert_java(Env.project_file("experiments/comprehension_arvan2026/files/FileSystemUtils"))
        cyclomatic = CyclomaticComplexity(LOG)
        expected = {"FileSystemUtils_deleteRecursively": 3,  # two early-return ifs
                    "FileSystemUtils$1_visitFile": 1,
                    "FileSystemUtils$1_postVisitDirectory": 1}
        for name, complexity in expected.items():
            with self.subTest(method=name):
                self.assertIn(name, graphs)
                self.assertEqual(complexity, cyclomatic.evaluate(graphs[name]))


# function: (cyclomatic, NPath, APC growth class), derived by hand from the source.
CONSISTENT_CONSTRUCTS = {
    "straight": (1, 1, "constant"),
    "if_chain": (4, 4, "constant"),
    "for_loop": (2, 2, "polynomial of degree 1"),
    "nested_loops": (3, 3, "exponential"),
    "while_break": (3, 3, "polynomial of degree 1"),
    "early_return": (3, 3, "constant"),
    "and_condition": (3, 3, "constant"),
    "ternary": (2, 2, "constant"),
    "int_switch": (4, 4, "constant"),
}


class TestCrossFrontEndConsistency(unittest.TestCase):
    """Equivalent C and Java functions get the same metrics."""

    @classmethod
    def setUpClass(cls) -> None:
        """Convert both halves of the consistency fixture."""
        cls.c_graphs = convert_c(fixture("consistency"))
        cls.java_graphs = {name.removeprefix("Consistency_"): graph
                           for name, graph in convert_java(fixture("Consistency")).items()}

    def test_fixtures_define_the_same_functions(self) -> None:
        """Both fixtures define exactly the asserted functions (plus Java's constructor)."""
        self.assertEqual(set(CONSISTENT_CONSTRUCTS), set(self.c_graphs))
        self.assertEqual(set(CONSISTENT_CONSTRUCTS) | {"init"}, set(self.java_graphs))

    def test_metrics_agree(self) -> None:
        """Cyclomatic, NPath, and APC growth class agree with each other and the hand derivation."""
        cyclomatic, npath, path = CyclomaticComplexity(LOG), NPathComplexity(LOG), PathComplexity(LOG)
        for function, expected in CONSISTENT_CONSTRUCTS.items():
            for language, graphs in (("C", self.c_graphs), ("Java", self.java_graphs)):
                with self.subTest(function=function, language=language):
                    graph = graphs[function]
                    self.assertEqual(expected, (cyclomatic.evaluate(graph), npath.evaluate(graph),
                                                growth_class(path.evaluate(graph)[0])))


class TestToolDiscovery(unittest.TestCase):
    """Env finds clang and opt from overrides, PATH, and versioned names, or explains what is missing."""

    def setUp(self) -> None:
        """Forget cached tool paths now and after the test; give each test an empty bin dir."""
        self.clear_tool_cache()
        self.addCleanup(self.clear_tool_cache)
        bin_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(bin_dir.cleanup)
        self.bin = os.path.realpath(bin_dir.name)

    @staticmethod
    def clear_tool_cache() -> None:
        """Drop the functools.cache'd tool paths."""
        Env.clang.cache_clear()
        Env.opt.cache_clear()

    def fake_tool(self, name: str) -> str:
        """Create an executable named `name` in the bin dir."""
        path = join(self.bin, name)
        with open(path, "w") as tool:
            tool.write("#!/bin/sh\n")
        os.chmod(path, 0o755)
        return path

    def environment(self, **variables: str):
        """Patch os.environ: PATH is the bin dir, METRINOME_* unset unless given."""
        patch = mock.patch.dict(os.environ, {"PATH": self.bin, **variables})
        patch.start()
        self.addCleanup(patch.stop)
        for name in ("METRINOME_CLANG", "METRINOME_OPT"):
            if name not in variables:
                os.environ.pop(name, None)

    def test_overrides_are_honored(self) -> None:
        """METRINOME_CLANG and METRINOME_OPT win over PATH."""
        self.fake_tool("clang")
        self.fake_tool("opt")
        clang, opt = self.fake_tool("my-clang"), self.fake_tool("my-opt")
        self.environment(METRINOME_CLANG=clang, METRINOME_OPT=opt)
        self.assertEqual(clang, Env.clang())
        self.assertEqual(opt, Env.opt())

    def test_opt_next_to_overridden_clang(self) -> None:
        """Without METRINOME_OPT, the opt beside the selected clang is used."""
        clang, opt = self.fake_tool("clang"), self.fake_tool("opt")
        self.environment(METRINOME_CLANG=clang)
        self.assertEqual(opt, Env.opt())

    def test_versioned_tools_on_path(self) -> None:
        """Debian-style clang-NN/opt-NN are found when there is no plain clang."""
        clang, opt = self.fake_tool("clang-17"), self.fake_tool("opt-17")
        self.environment()
        self.assertEqual(clang, Env.clang())
        self.assertEqual(opt, Env.opt())

    def test_missing_clang(self) -> None:
        """No clang anywhere: ToolNotFoundError naming the override variable."""
        self.environment()
        with self.assertRaises(ToolNotFoundError) as raised:
            Env.clang()
        self.assertIn("METRINOME_CLANG", str(raised.exception))

    def test_missing_opt(self) -> None:
        """A clang without opt: ToolNotFoundError naming the override variable."""
        self.environment(METRINOME_CLANG=self.fake_tool("clang"))
        with self.assertRaises(ToolNotFoundError) as raised:
            Env.opt()
        self.assertIn("METRINOME_OPT", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
