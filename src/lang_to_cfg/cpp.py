"""This module converts C++ source code into Graph objects representing the CFG for the code."""

import os
import re
import shlex
import subprocess
from typing import Optional

import glob2  # type: ignore

from core.env import Env, KnownExtensions
from core.log import Log
from graph.control_flow_graph import ControlFlowGraph, Metadata
from graph.graph import EdgeListGraph
from lang_to_cfg import converter

# Diagnostics that clang 14 reported as warnings but clang 16+ reports as errors by default.
LEGACY_C_DIAGNOSTICS = ("implicit-function-declaration", "implicit-int", "int-conversion",
                        "incompatible-function-pointer-types")


class CPPConvert(converter.ConverterAbstract):
    """Create Graph objects from files."""

    # pylint: disable=super-init-not-called
    def __init__(self, logger: Log) -> None:
        """Create a new instance of the C++ converter."""
        self.logger = logger
        self._edge_pattern = "->"
        self._name_pattern = "([a-zA-Z0-9]+ )"
        self._optimize = False
        # self._call_pattern = r"(@_)[A-Z0-9]{2,}[A-Za-z0-9_]*\("
        # TODO: merge in david's code to correct parsing and other graph conversions
        # For now, this ignores the _Z6 prefix that was previously matched,
        # and we remove the underscore after @
        # this fix was needed to make clang work (instead of clang++)
        self._call_pattern = r"(@)[A-Za-z0-9_]*\("

    def name(self) -> str:
        """Get the name of the CPP converter."""
        return "CPP"

    def to_graph(self,
                 filename: str,
                 file_extension: str,
                 simplify: bool = False) -> Optional[dict[str, ControlFlowGraph]]:
        """Create a CFG from a C++ source file."""
        Env.make_temp()
        Env.clean_temps()
        self.logger.d_msg(f"Creating dot files for {filename}, {file_extension}")
        self.create_dot_files(filename, file_extension, simplify)
        self.logger.d_msg("Converting to standard format")
        file_count = self.convert_to_standard_format(filename)
        self.logger.d_msg(f"File count is: {file_count}")
        if file_count == 0:
            Env.clean_temps()
            return None

        name = os.path.split(filename)[1]
        graphs: dict[str, ControlFlowGraph] = {}
        filename = f"{Env.TMP_DOT_PATH}/{name}"
        files = glob2.glob(f"{Env.TMP_DOT_PATH}/*.dot")
        for file in files:
            graph_name = os.path.basename(file)
            self.logger.d_msg(f"graph_name: {graph_name}")
            graph = ControlFlowGraph.from_file(file, EdgeListGraph,
                                               [Metadata.with_language(KnownExtensions.C)])
            graphs[graph_name] = graph
        Env.clean_temps()
        return graphs

    def parse_original(self, file: str) -> tuple[list[str], list[str],
                                                 dict[str, str], int]:
        """Obtain all of the Graph information from an existing dot file in the original format."""
        # Read the original files.
        nodes, edges = [], []
        node_map: dict[str, str] = {}
        counter = 0

        with open(file, "r") as old_file:
            content = old_file.readlines()
            for line in content[1:]:
                line = line.strip()
                # print(line)

                # Throw out the label (e.g. label="CFG for 'main' function")
                # for the graph and remove whitespace.
                if line.startswith("label") or line == "":
                    continue

                # If it contains a label (denoted by '[]'), it is a vertex.
                is_edge = re.search(self._edge_pattern, line)
                if is_edge is None:
                    node_name = re.match(self._name_pattern, line.lstrip())
                    if node_name is None:

                        continue

                    node_name_str = node_name.groups()[0].strip()
                    node_map[node_name_str] = str(counter)
                    node_to_add = str(counter)
                    calls = re.finditer(self._call_pattern, line.lstrip())
                    label = ""
                    call_label = ""
                    for call in calls:
                        call_label += " "
                        call_label += call.group(0)[1:-1]
                    if counter == 0 and call_label != "":
                        label = f" [label=\"START CALLS{call_label}\"]"
                    elif counter == 0:
                        label = " [label=\"START\"]"
                    elif call_label != "":
                        label = f" [label=\"CALLS{call_label}\"]"
                    node_to_add += label
                    # print(label)
                    # print(node_to_add)
                    nodes.append(node_to_add)

                    counter += 1
                else:
                    edges += [line]
            # print(node_map)
            # print(edges)
        return nodes, edges, node_map, counter

    def convert_file_to_standard(self, file: str,
                                 filename: str) -> None:
        """Convert a single file to the standard format."""
        nodes, edges, node_map, counter = self.parse_original(file)
        # Covers case of leaf CFGs.
        if len(nodes) == 1:
            nodes.append("1")
            nodes.append("2")
            edges += ["0 -> 1;"]
            edges += ["1 -> 2;"]
            counter += 2

        # Make a temporary file (with the new content), e.g. tmp_dot/<source>_.<function>.dot
        source_name = os.path.basename(filename)
        f_name = os.path.basename(file)
        with open(Env.TMP_DOT_PATH + "/" + source_name + "_" + f_name, 'w+') as new_file:
            new_file.write("digraph { \n")

            # Create the nodes and then the edges.
            for i, node in enumerate(nodes):
                if i == counter - 1:
                    node += " [label=\"EXIT\"]"
                new_file.write(node + ";" + "\n")

            node_ref = re.compile(r"(Node0x[0-9a-f]+)(?::s\d+)?")
            for edge in edges:
                # Map LLVM node names to indices and drop record ports (":s0", ":s1", ... one per successor).
                new_file.write(node_ref.sub(lambda match: node_map[match.group(1)], edge) + "\n")
            new_file.write("}")
            new_file.seek(0)

    def convert_to_standard_format(self, filename: str) -> int:
        """
        Convert the generated .dot files to a common format.

        Each dot file generated from the .cpp source is converted to the same format
        as the dot files generated from Java CFGs.
        """
        files = []
        for name in glob2.glob(f"{Env.TMP_PATH}/.*.dot"):
            if "global" in name.lower():
                os.remove(name)
            else:
                files.append(name)
        self.logger.d_msg(f"CFG files: {files}")

        for file in files:
            self.convert_file_to_standard(file, filename)

        return len(files)

    def create_dot_files(self, filepath: str, file_extension: str, simplify: bool = False) -> None:
        """Create a .dot file in Env.TMP_PATH representing the CFG of each function in a C/C++ file."""
        # Make sure the file extension begins with a '.'
        if file_extension[0] != '.':
            file_extension = f".{file_extension}"
        source = f"{filepath}{file_extension}"
        # At -O0 clang marks every function optnone, and the new pass manager skips its printers on
        # optnone functions, so drop the attribute. The emitted CFG is otherwise unchanged.
        # clang 16+ turned these legacy-C diagnostics into errors; keep them warnings, as in clang 14.
        compile_cmd = [Env.clang(), "-emit-llvm", "-S", "-Xclang", "-disable-O0-optnone",
                       *(f"-Wno-error={diagnostic}" for diagnostic in LEGACY_C_DIAGNOSTICS),
                       source, "-o", "-"]
        if self._optimize:
            compile_cmd.insert(3, "-O3")
        # Under the legacy pass manager, -simplifycfg skipped optnone (-O0) functions, so `simplify`
        # only ever affected -O3 builds. Keep that behavior so published results stay reproducible.
        passes = "simplifycfg,dot-cfg" if simplify and self._optimize else "dot-cfg"
        self.logger.d_msg(f"Command: {shlex.join(compile_cmd)} | {Env.opt()} -passes={passes}")

        compiled = subprocess.run(compile_cmd, capture_output=True, text=True, check=False)
        if compiled.returncode != 0:
            self.logger.e_msg(f"clang failed on {source}:\n{compiled.stderr}")
            return
        if compiled.stderr:
            self.logger.d_msg(compiled.stderr)
        # opt writes one ".<function>.dot" file per function into its working directory.
        printed = subprocess.run([Env.opt(), f"-passes={passes}", "-disable-output"], input=compiled.stdout,
                                 cwd=Env.TMP_PATH, capture_output=True, text=True, check=False)
        if printed.returncode != 0:
            self.logger.e_msg(f"opt failed on {source}:\n{printed.stderr}")
