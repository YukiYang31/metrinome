# Metrinome user guide

Metrinome turns source code into control flow graphs (CFGs) and computes complexity metrics on them:
cyclomatic complexity, NPath complexity, (asymptotic) path complexity, and exact path counts up to a
length bound. It can also run the symbolic execution engine KLEE on C functions.

This guide covers using Metrinome. To change Metrinome itself, see the
[development guide](development-guide.md).

- [Installing](#installing)
- [Starting the REPL](#starting-the-repl)
- [A first session](#a-first-session)
- [Metrics](#metrics)
- [Command reference](#command-reference)
- [KLEE](#klee)
- [Reproducing the papers](#reproducing-the-papers)
- [Files Metrinome writes](#files-metrinome-writes)
- [Tips](#tips)
- [Troubleshooting](#troubleshooting)

## Installing

You need Python 3.10 or newer and, depending on the languages you analyse:

| To analyse | You need |
|---|---|
| C, C++ | clang and the matching LLVM `opt`, version 14 or newer |
| Java | a JDK, version 8 or newer (`javac` and `java`) |
| Python | nothing else |
| C with KLEE | KLEE 3.0 or newer and a clang of KLEE's LLVM version (see [KLEE](#klee)) |

```bash
git clone https://github.com/YukiYang31/metrinome.git
cd metrinome
pip install -r requirements.txt
```

On Ubuntu, `sudo apt install clang-14 llvm-14 openjdk-17-jdk-headless` provides the tools. Without root access,
conda-forge has all of them:

```bash
micromamba create -p ./toolchain -c conda-forge clang llvm-tools openjdk
export PATH="$PWD/toolchain/bin:$PATH"
```

Metrinome finds its tools on `PATH`. If you have several versions installed, or tools outside `PATH`, select
them with environment variables:

| Variable | Selects | Default |
|---|---|---|
| `METRINOME_CLANG` | clang for C/C++ | `clang`, else the newest `clang-NN` on `PATH` |
| `METRINOME_OPT` | LLVM `opt` | the `opt` next to the selected clang, else `opt` on `PATH` |
| `JAVA_HOME` | JDK | `javac`/`java` on `PATH` |
| `METRINOME_KLEE` | KLEE | `klee` on `PATH` |
| `METRINOME_KLEE_INCLUDE` | KLEE headers | the `include/` directory of the KLEE installation |
| `METRINOME_KLEE_CLANG` | clang for KLEE bitcode | `clang-N` for KLEE's LLVM version N, else the selected clang if not newer |
| `METRINOME_FAKE_LIBC` | pycparser's fake libc headers (used by `to_klee_format`) | the `pycparser-fake-libc` package |
| `METRINOME_HOME` | where temporary files and exports go | the `src/` directory of the checkout |

A Docker image with every tool, including KLEE, is also available. It is optional:

```bash
docker build -t apcmetrinome/develop:latest -f src/Dockerfile .
cd src && make run      # a shell in the image, with src/ mounted at /app/code
```

## Starting the REPL

```bash
python3 src/main.py [flags]
```

| Flag | Effect |
|---|---|
| `--interprocedural` | `metrics` computes interprocedural path complexity, which accounts for the functions a function calls, instead of the intraprocedural metrics |
| `--recursion` | `metrics` computes recursive path complexity for functions that call themselves |
| `--path-length K` | length bound of the "paths of length <= K" metric (default 50) |
| `--poor` | plain text output instead of tables |
| `--debug` | verbose output, and enables the `reload` command |

The prompt shows the REPL's current directory. Relative paths in commands are resolved against it. It
starts as the directory you launched from, and `cd` changes it.

## A first session

```
convert tests/fixtures/switch4.c
list graphs
metrics *
show graph switch4_.classify.dot
export metrics *
quit
```

1. `convert` compiles the file and creates one graph per function. Graph names have the form
   `<file>_.<function>.dot` for C and C++. Java graph names are the paths of the extracted `.dot` files (for
   example `.../tmp_dot/Consistency/Consistency_if_chain_0_basic.dot`); select them with `*` or a regular expression.
2. `metrics *` computes every metric for every graph and prints a table per graph.
3. `export metrics *` writes all results to `src/exports/metrics.csv`.

## Metrics

`metrics <name>` computes the following for each graph:

| Metric | Meaning |
|---|---|
| Cyclomatic Complexity | the number of linearly independent paths, E − V + 2 |
| NPath Complexity | the number of acyclic execution paths, with each loop body taken at most once |
| Path Complexity | APC: the asymptotic growth of the number of paths as a function of path length n, e.g. `O(n)` or `O(1.618**n)`. Path Complexity: the closed-form expression for that count |
| Paths of length <= K | the exact number of paths from entry to exit with at most K edges (`--path-length`) |
| Lines of Code | Python graphs only |

The modes change what `metrics` computes:

- **`--recursion`:** a function that calls itself gets Recursive Path Complexity instead of Path Complexity.
- **`--interprocedural`:** each function gets Function Call Path Complexity (the call graph's functions are
  stitched in), its naive variant, and Recursive Path Complexity. Convert every file containing callees
  first, because callees are looked up among the graphs already loaded.

Each metric has a time limit of 6000 seconds per graph.

## Command reference

`help` lists the commands, and `help <command>` shows a command's usage. Types used by `list`, `show`,
`delete`, and `export` are `graph`, `metric`, `klee_file`, `klee_bc`, `klee_stat`, `klee` (all KLEE objects
of a name), and `*` (all types). Plural forms (`graphs`) work too.

### convert

Converts source files to CFGs. It accepts a file, a directory (every supported file in it), or several paths.
Supported extensions: `.c`, `.cpp`, `.java`, `.class`, `.jar`, `.py`.

```
convert <file-or-directory> [<file-or-directory> ...]
convert -r <directory>       # also convert files in subdirectories
convert -i <file.c>          # inline called functions first, then convert
convert -h <file.c>          # heuristic inlining, then convert
convert -gs <file>           # also stitch all functions into one graph, <file>-full
```

C and C++ give block-level CFGs: clang compiles the file without optimisation and LLVM prints each
function's CFG. Java gives block-level CFGs of every method of every class, including nested and
anonymous classes. Python gives statement-level CFGs and supports a subset of the language: assignment,
expressions, `if`/`elif`/`else`, `return`, `while`, and `with`. Comprehensions, lambdas, and
`try`/`raise` are not supported.

### import

Loads `.dot` CFG files, such as ones written by `export graph`, as graphs. It accepts the same path forms
as `convert`, including `-r`.

```
import <file-or-directory> [...]
```

### list

```
list <type>
```

Lists the names of the objects of a type, for example `list graphs` or `list metrics`.

### show

```
show <type> <name>
```

Prints an object. A graph prints its nodes, edges, and entry and exit nodes. Both `<type>` and `<name>`
accept `*`.

### metrics

```
metrics <name>
metrics *
metrics <regular expression>
```

Computes the [metrics](#metrics) for one graph, all graphs, or every graph whose name matches the
regular expression.

### export

```
export <type> <name>
```

Writes objects to `src/exports/` (or `$METRINOME_HOME/exports/`):

| Command | Output |
|---|---|
| `export graph <name>` | `<name>_export.dot`, with `/` and `.` in the name replaced by `_` (e.g. `switch4__classify_dot_export.dot`); with `*`, one `<file name>.dot` per graph, named the same way |
| `export metrics *` | `metrics.csv`, with columns `graph_name`, `apc`, `cyclo`, `npath`, `bounded_paths` |
| `export metrics <name>` | `<name>_export_metrics`, the raw results |
| `export klee_file <name>` | `<name>_export_klee.c`, the generated KLEE harness |
| `export klee_bc <name>` | `<name>_export.bc` |
| `export klee_stat <name>` | `<name>_export_kleestat.c`, the KLEE statistics |

### delete

```
delete <type> <name>
```

Removes an object from memory. `delete klee <name>` removes all KLEE objects with that name, and
`delete * <name>` removes everything with that name.

### run_experiment

```
run_experiment <directory> <output>
```

Converts every supported file under the directory (recursively), computes all metrics, and writes `<output>.csv`.

### Files and directories

`cd`, `ls`, `pwd`, `mkdir`, `mv`, and `rm` work like their shell equivalents on the REPL's current directory.

### reload and quit

`reload`, available only with `--debug`, reloads the command implementations without losing loaded objects.
`quit` exits and saves the command history. Ending the REPL any other way can lose the history.

## KLEE

[KLEE](https://klee-se.org) is a symbolic execution engine: it explores a program's paths and writes a test
input for each one it completes. Metrinome generates a KLEE harness for each function in a C file, runs
KLEE on it, and replays the resulting tests.

### Installing KLEE

On Ubuntu, follow KLEE's [build instructions](https://klee-se.org/build/). Then install the clang that has
KLEE's LLVM version (for example `clang-18`); Metrinome finds `clang-N` automatically. Without root access,
KLEE builds against conda-forge's LLVM in a few minutes:

```bash
micromamba create -p ./klee-env -c conda-forge llvmdev=18 clang=18 clangxx=18 llvm-tools=18 libz3 sqlite zlib
git clone --depth 1 --branch v3.3 https://github.com/klee/klee.git
cmake -S klee -B klee-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PWD/klee-install" \
  -DCMAKE_PREFIX_PATH="$PWD/klee-env" -DLLVMCC="$PWD/klee-env/bin/clang" -DLLVMCXX="$PWD/klee-env/bin/clang++" \
  -DCMAKE_INSTALL_RPATH="$PWD/klee-env/lib" -DENABLE_SOLVER_Z3=ON -DENABLE_SOLVER_STP=OFF -DENABLE_TCMALLOC=OFF \
  -DENABLE_UNIT_TESTS=OFF -DENABLE_SYSTEM_TESTS=OFF -DENABLE_DOCS=OFF
cmake --build klee-build -j && cmake --install klee-build
export PATH="$PWD/klee-install/bin:$PATH" METRINOME_KLEE_CLANG="$PWD/klee-env/bin/clang"
```

The Docker image already contains KLEE 3.3.

### Running KLEE from the REPL

```
to_klee_format tests/cFiles/fse_2020_benchmark/03_sign.c
klee_to_bc *
klee *
show klee_stat *
klee_replay sign
```

| Command | Effect |
|---|---|
| `to_klee_format <file.c>` | For each function with parameters, generates a harness: a `main()` that declares each parameter, marks it symbolic with `klee_make_symbolic`, and calls the function. Array parameters get `SIZE` = 10 elements. Use `-r` for a directory. |
| `klee_to_bc <name>` or `*` | Compiles harnesses to LLVM bitcode with the KLEE-compatible clang |
| `klee <name>` or `*` `[klee options]` | Runs KLEE (30 s search limit, 60 s overall) and records generated tests, completed paths, instructions, and time. Tests go to `src/klee_out/<name>/tests/`. |
| `klee <file.bc> [klee options]` | Runs KLEE on your own bitcode; KLEE writes `klee-out-N/` next to the file |
| `klee_replay <name>` | Runs the function natively on each test's inputs and prints the inputs and the exit status |
| `klee_replay <file.ktest>` | Replays one test |

For `sign`, KLEE finds three paths, and replay shows inputs 1, 0, and INT_MIN with exit statuses 1, 0, and 255.
The exit status is the function's return value modulo 256, so −1 appears as 255.

Functions that read input or depend on other files may need manual changes before KLEE can run them. The
harness `#include`s the original file, so KLEE needs to find every header that file includes.

## Reproducing the papers

`src/Benchmark.sh` reproduces the published results. It opens a menu that asks for the paper and then the metric:

```bash
bash src/Benchmark.sh
```

| Menu entry | Paper | Programs |
|---|---|---|
| 1 | ICSE 2021 | `src/experiments/icse_experiment/files` |
| 2 | FormaliSE 2023 | `src/experiments/recursion/files` |
| 3 | ICSE 2024 poster | `src/experiments/function_calls/benchmark` |
| 4 | ISSTA 2024 | `src/tests/cFiles/C-master` |
| 5 | | the REPL |

The metric choices are interprocedural APC, naive interprocedural APC, recursive APC, NPath, or all of them.
Results are written to `src/experiments/function_calls/data/`. The test suite checks the ICSE 2021 and ISSTA 2024
results automatically ([development guide](development-guide.md#tests)).

Other experiments live under `src/experiments` and `src/klee`. Run them with `PYTHONPATH=src` after installing
`requirements-dev.txt`:

| Script | What it does |
|---|---|
| `src/experiments/comprehension_arvan2026/data_collection.py` | correlates Metrinome's metrics on the 8 snippets of Arvan et al. (ASE 2026) with expert comprehensibility ranks, for both the Java originals and C translations; writes `data/metrics.csv` and `data/correlations.csv` |
| `src/klee/klee_experiment.py normal` | KLEE coverage, paths, and tests versus search depth for the 30 functions in `src/tests/cFiles/fse_2020_benchmark`; CSVs go to `frames/`, plots to `graphs/` |
| `src/klee/klee_experiment.py optimized` | the same, also with `-O3` |
| `src/klee/klee_experiment.py time_test` | KLEE statistics versus time limit for Newton's method |
| `src/analyze/analyze_manual.py`, `analyze_automatic.py` | fit growth functions (polynomial, exponential) to the KLEE data, with manual or automatic breakpoints |

With large depths KLEE starts timing out and the completed-path counts stop being meaningful. The analysis
scripts exist to find where that happens.

## Files Metrinome writes

| Location | Contents |
|---|---|
| `src/tmp/`, `src/tmp_dot/` | intermediate files of the current conversion, cleared on each conversion |
| `src/exports/` | files written by `export` |
| `src/klee_out/<name>/` | the bitcode and KLEE tests of `klee <name>` |
| `repl_log.log` | the debug log, in the directory you started the REPL from |
| `~/.history` | the REPL command history |

All `src/` locations move to `$METRINOME_HOME` when it is set.

## Tips

- Arrow keys recall earlier commands, including from earlier sessions.
- To look at a graph, `export graph <name>` and open the `.dot` file with `xdot`, Graphviz (`dot -Tpng`), or
  GraphvizOnline.
- The files under `src/tests/` (for example `src/tests/cFiles`) are small examples that are handy for trying
  out commands.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `clang not found. Install clang ... or set METRINOME_CLANG.` (similar for `opt`, `javac`, `klee`) | The tool is not on `PATH`. Install it or set the variable named in the message. |
| `Conversion failed` for a C file | Run with `--debug` to see clang's error. A file whose functions are all C99 `inline` (without `static` or `extern`) has no function definitions to analyse; compile it with the function used from another file, or remove `inline`. |
| `KLEE uses LLVM 18 and cannot read bitcode from newer LLVM` | KLEE can only read bitcode from its own LLVM version or older. Install `clang-18` (the version in the message) or set `METRINOME_KLEE_CLANG`. |
| `KLEE headers not found` | KLEE was run from its build directory. Set `METRINOME_KLEE_INCLUDE` to `<klee source>/include`. |
| `Timeout!` from `metrics` | A metric exceeded 6000 s, which happens for very large interprocedural graphs. |
| Old C code fails with clang 16 or newer | Metrinome already turns the new clang 16 errors for implicit `int`, implicit declarations, and int/pointer conversions back into warnings. Other errors are real compile errors. |
