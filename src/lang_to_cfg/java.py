"""This class knows how to convert from java source code to graph objects."""
import re
import subprocess
from functools import cache
from typing import Optional

from glob2 import glob  # type: ignore

from core.env import Env, KnownExtensions
from core.log import Log
from graph.control_flow_graph import ControlFlowGraph, Metadata
from graph.graph import EdgeListGraph
from lang_to_cfg import converter


@cache
def _javac_release_flags() -> tuple[str, ...]:
    """Flags making javac emit Java 8 class files, the newest version the CFG extractor's ASM reads."""
    version = subprocess.run([Env.java("javac"), "-version"], capture_output=True, text=True, check=False)
    match = re.search(r"javac (\d+)", version.stdout + version.stderr)
    if match is None or int(match.group(1)) == 1:  # JDK 8 reports "javac 1.8.0_x"
        return ()
    return ("--release", "8", "-Xlint:-options")


class JavaConvert(converter.ConverterAbstract):
    """
    JavaConvert is able to convert java files to graphs.

    Interacts with the java program that extracts CFGs from Java source code.
    """

    # pylint: disable=super-init-not-called
    def __init__(self, logger: Log) -> None:
        """Create a new Java converter."""
        self.logger: Log = logger
        self._output_folder = Env.TMP_DOT_PATH
        self._input_folder = Env.TMP_PATH

    def name(self) -> str:
        """Get the name of the Java converter."""
        return "Java"

    # pylint: disable=R0201
    def to_graph(self, filename: str, file_extension: str) -> Optional[dict[str, ControlFlowGraph]]:
        """Create a CFG for every method of every class in a Java source file, .class file, or .jar."""
        Env.clean_temps()

        check_ending = filename.endswith('sources') or filename.endswith('javadoc') or \
            filename.endswith('tests')
        if file_extension == '.jar' and check_ending:
            return None

        path = ""
        fname = filename + file_extension
        self.logger.v_msg(f"processing {fname}")
        output_path = Env.get_output_path(fname)

        if file_extension == ".jar":
            self.runcmd(f"jar xf {fname}", cwd=self._input_folder)
            output_path = Env.get_output_path(self._input_folder)
            fname = self._input_folder
            path = f"{self._output_folder}/tmp/*.dot"

        if file_extension == ".java":
            compiled = subprocess.run([Env.java("javac"), *_javac_release_flags(), fname, "-d", self._input_folder],
                                      capture_output=True, text=True, check=False)
            if compiled.returncode != 0:
                self.logger.e_msg(f"javac failed on {fname}:\n{compiled.stderr}")
                return None
            # Analyse every class javac produced, including nested and anonymous ones (Outer$1.class).
            fname = self._input_folder

        cmd = f"{Env.java('java')} -jar {Env.CFG_EXTRACTOR_JAR} -i {fname} -o {output_path}"
        if (err := self.runcmd(cmd, cwd=Env.PROJECT_PATH)[1]) is not None:
            error = str(err)
            if "FileNotFoundException" in error:
                self.logger.e_msg(f"Java was unable to generate {fname}")
                return None

        self.logger.d_msg("Generated .dot files")

        graphs = {}
        if path == "":
            path = f"{output_path}/*.dot"

        dot_files = glob(path)
        for file in dot_files:
            graphs[file] = ControlFlowGraph.from_file(file, EdgeListGraph,
                                                      [Metadata.with_language(KnownExtensions.Java)])
        Env.clean_temps()
        return graphs
