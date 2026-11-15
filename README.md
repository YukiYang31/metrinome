<img src="resources/Metrinome.svg" height="100">

[![CI](https://github.com/YukiYang31/metrinome/actions/workflows/ci.yml/badge.svg)](https://github.com/YukiYang31/metrinome/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

## Overview

Metrinome is an all-purpose tool for working with code complexity metrics. It can be used as both a REPL and API, and includes:

- Converters to turn C, C++, Java, and Python code into control flow graphs (CFGs)
- Metric calculators for NPath, Cyclomatic, and (asymptotic) Path Complexity, including interprocedural and recursive path complexity
- The exact number of paths up to a given execution length (`--path-length K`, default 50), the quantity path complexity bounds asymptotically
- KLEE integration: generate a symbolic-execution harness for each C function, run KLEE on it, and replay the generated tests

<img src="resources/repl_screenshot.png" height="300">

## Documentation

- [User guide](docs/user-guide.md): installing, the REPL commands, metrics, KLEE, reproducing the papers, troubleshooting
- [Development guide](docs/development-guide.md): architecture, extending Metrinome, tests, CI, reproducibility rules

## Getting started

### Native

Requirements:

- Python 3.10 or newer
- clang and the matching LLVM `opt`, version 14 or newer (for C/C++)
- a JDK, version 8 or newer (for Java; `javac` and `java`)

```bash
pip install -r requirements.txt
python3 src/main.py            # start the REPL; flags: --interprocedural, --recursion, --path-length K, --poor, --debug
```

Inside the REPL, for example:

```
convert path/to/file.c
metrics *
export metrics *
```

Exports are written to `src/exports/`.

Metrinome finds its tools on `PATH`. Override them with environment variables when needed:

| Variable | Default |
|---|---|
| `METRINOME_CLANG` | `clang`, else the newest `clang-NN` on `PATH` |
| `METRINOME_OPT` | the `opt` installed next to the selected clang, else `opt` on `PATH` |
| `JAVA_HOME` | `javac`/`java` on `PATH` |
| `METRINOME_HOME` | the `src/` directory of this checkout (temporary and export files live here) |
| `METRINOME_KLEE` | `klee` on `PATH`; `klee-stats`, `ktest-tool`, headers and `libkleeRuntest` come from the same installation |
| `METRINOME_KLEE_INCLUDE` | the `include/` directory of that installation |
| `METRINOME_KLEE_CLANG` | `clang-N` where N is KLEE's LLVM version, else the selected clang if it is not newer (KLEE cannot read bitcode from a newer LLVM) |

On Ubuntu: `sudo apt install clang-14 llvm-14 openjdk-17-jdk-headless`. Without root, conda-forge provides everything:
`micromamba create -p ./toolchain -c conda-forge clang llvm-tools openjdk` and then add `./toolchain/bin` to `PATH`.

### Docker

```bash
docker build -t apcmetrinome/develop:latest -f src/Dockerfile .
cd src && make run             # mounts src/ at /app/code and starts a shell in the image
```

The development image also contains KLEE 3.3.

The self-contained replication image (`replication/Dockerfile`) copies the sources in and opens the paper benchmark menu.

## KLEE

KLEE is optional; only the `to_klee_format`, `klee_to_bc`, `klee` and `klee_replay` commands and `src/klee/` need it.
Install KLEE 3.0 or newer with a clang of the same LLVM version; the [user guide](docs/user-guide.md#klee) shows a
no-root build against conda-forge's LLVM 18 and the REPL workflow:

```
to_klee_format path/to/file.c   # one harness per function: parameters become symbolic inputs
klee_to_bc *                    # compile the harnesses to bitcode
klee *                          # run KLEE; tests go to src/klee_out/<function>/tests
klee_replay <function>          # run the function natively on each test's inputs
```

## Paper benchmarks

`src/Benchmark.sh` reproduces the published results (ICSE 2021, FormaliSE 2023, ICSE 2024 poster, ISSTA 2024):

```bash
bash src/Benchmark.sh
```

Experiment scripts under `src/experiments` import Metrinome's modules, so run them with `PYTHONPATH=src`.

## Tests

```bash
pip install -r requirements-dev.txt
cd src && python3 -m unittest discover -s tests -t .
```

The suite includes regression tests that pin the published ICSE 2021 and ISSTA 2024 results. CI runs it on every push.

## Links

- **Documentation** [user guide](docs/user-guide.md), [development guide](docs/development-guide.md)
  (they supersede the 2021 [wiki](https://github.com/hmc-alpaqa/metrinome/wiki))
- **DockerHub** https://hub.docker.com/repository/docker/harveymudd/metrinome
- **Initial Paper** https://www.cs.hmc.edu/~bang/research/metrinome.pdf
