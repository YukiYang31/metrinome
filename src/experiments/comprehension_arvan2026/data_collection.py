"""Compare Metrinome's metrics with the expert comprehensibility ranking of Arvan et al. (ASE 2026).

"On the Reliability of Code Comprehension Proxies", https://doi.org/10.1145/3832783.3834425.
Snippets (from the replication package, https://doi.org/10.5281/zenodo.21218362):
  files/*.java    original Java methods, analysed via the Java bytecode CFG extractor
  files_c/*.c     manual C translations, analysed via clang/LLVM (as in Dissem et al., ICPC 2023)
Ground truth: data/ground_truth.csv (expert Delphi round-3 ranks and per-snippet student proxies).

Each metric is correlated with the expert mean rank using Kendall's tau-b, the statistic used in the
paper. Output: data/metrics.csv (per snippet, both languages) and data/correlations.csv.
"""
import math
import os
import re
import time
from itertools import combinations
from typing import Callable, Optional

import pandas as pd  # type: ignore
from sympy import Poly, symbols, sympify  # type: ignore

from core.log import Log
from core.env import Env
from lang_to_cfg.converter import ConverterAbstract
from lang_to_cfg.cpp import CPPConvert
from lang_to_cfg.java import JavaConvert
from metric import cyclomatic_complexity, npath_complexity, path_complexity
from utils import Timeout

BASE_PATH = Env.project_file("experiments/comprehension_arvan2026")
N_VAR = symbols("n")
METRICS = ["cyclo", "npath", "apc_rank"]

# language -> (source path without extension, extension, CFG file name) for a ground-truth row
SOURCES: dict[str, Callable[[pd.Series], tuple[str, str, str]]] = {
    "java": lambda row: (f"{BASE_PATH}/files/{row['class']}", ".java",
                         f"{row['class']}_{row['method']}_0_basic.dot"),
    "c": lambda row: (f"{BASE_PATH}/files_c/{row['snippet']}_{row['method']}", ".c",
                      f"{row['snippet']}_{row['method']}_.{row['method']}.dot"),
}


def apc_order_key(apc: object) -> Optional[tuple[float, ...]]:
    """Map an APC result to a sortable growth-order key: constants < polynomials < exponentials."""
    try:
        expr = sympify(str(apc))
    except Exception:  # pylint: disable=broad-except
        return None
    if N_VAR not in expr.free_symbols:
        return (0.0, float(expr))
    bases = [float(b) for b in re.findall(r"([0-9.]+)\*\*n", str(apc))]
    if bases and max(bases) > 1.0:
        return (2.0, max(bases))
    return (1.0, float(Poly(expr.subs(sympify("1.0**n"), 1), N_VAR).degree()))


def kendall_tau_b(xs: list, ys: list) -> float:
    """Kendall's tau-b with tie correction (same definition as scipy.stats.kendalltau)."""
    concordant = discordant = ties_x = ties_y = 0
    for (x1, y1), (x2, y2) in combinations(zip(xs, ys), 2):
        if x1 == x2 and y1 == y2:
            ties_x += 1
            ties_y += 1
        elif x1 == x2:
            ties_x += 1
        elif y1 == y2:
            ties_y += 1
        elif (x1 < x2) == (y1 < y2):
            concordant += 1
        else:
            discordant += 1
    total = len(xs) * (len(xs) - 1) / 2
    denom = math.sqrt((total - ties_x) * (total - ties_y))
    return (concordant - discordant) / denom if denom else float("nan")


def dense_rank(keys: list) -> list[int]:
    """Rank keys so that equal keys share a rank (1 = least complex)."""
    order = {key: i + 1 for i, key in enumerate(sorted(set(keys)))}
    return [order[key] for key in keys]


class DataCollector:
    """Compute Metrinome metrics for the eight study snippets."""

    def __init__(self) -> None:
        """Create a new instance of the data collector."""
        log = Log()
        self.converters: dict[str, ConverterAbstract] = {"java": JavaConvert(log), "c": CPPConvert(log)}
        self.apc_computer = path_complexity.PathComplexity(log)
        self.cyclo_computer = cyclomatic_complexity.CyclomaticComplexity(log)
        self.npath_computer = npath_complexity.NPathComplexity(log)

    # pylint: disable=broad-except
    def collect(self, truth: pd.DataFrame, lang: str) -> pd.DataFrame:
        """Compute the metrics of every snippet's method in one language; one row per snippet."""
        rows = []
        for _, snippet in truth.iterrows():
            source, extension, dot_name = SOURCES[lang](snippet)
            graphs = self.converters[lang].to_graph(source, extension)
            graph = next((g for key, g in (graphs or {}).items() if key.endswith(dot_name)), None)
            row = {"snippet": snippet["snippet"], "graph_name": dot_name}
            if graph is None:
                row["exception"] = "graph not found"
                rows.append(row)
                continue
            row["vertex_count"] = len(graph.graph.vertices())
            row["edge_count"] = len(graph.graph.edge_rules())
            row["cyclo"] = self.cyclo_computer.evaluate(graph)
            row["npath"] = self.npath_computer.evaluate(graph)
            start_time = time.time()
            try:
                with Timeout(300):
                    apc, path_compl = self.apc_computer.evaluate(graph)
                row["apc"], row["path_complexity"] = str(apc), str(path_compl)
            except Exception as exc:
                row["exception"] = repr(exc)
            row["apc_time"] = time.time() - start_time
            rows.append(row)
        data = pd.DataFrame(rows)
        data["apc_rank"] = dense_rank([apc_order_key(a) for a in data["apc"]])
        return data


def correlations(data: pd.DataFrame) -> pd.DataFrame:
    """Kendall tau-b of each metric (and the paper's student proxies) against the expert mean rank."""
    truth = list(data["expert_mean_rank"])
    rows = [{"measure": metric, **{lang: round(kendall_tau_b(truth, list(data[f"{metric}_{lang}"])), 4)
                                   for lang in SOURCES}}
            for metric in METRICS]
    rows += [{"measure": proxy, "student_proxy": round(kendall_tau_b(truth, list(data[proxy])), 4)}
             for proxy in ["student_time_output", "student_readTime", "student_scaleSM"]]
    return pd.DataFrame(rows)


def main() -> None:
    """Compute metrics in both languages, correlate with the expert ranking, and write the CSVs."""
    truth = pd.read_csv(f"{BASE_PATH}/data/ground_truth.csv")
    collector = DataCollector()
    data = truth
    for lang in SOURCES:
        metrics = collector.collect(truth, lang).add_suffix(f"_{lang}")
        data = data.merge(metrics.rename(columns={f"snippet_{lang}": "snippet"}), on="snippet")
    os.makedirs(f"{BASE_PATH}/data", exist_ok=True)
    data.to_csv(f"{BASE_PATH}/data/metrics.csv", index=False)
    corr = correlations(data)
    corr.to_csv(f"{BASE_PATH}/data/correlations.csv", index=False)
    cols = ["snippet", "method", "expert_mean_rank"] + [f"{m}_{lang}" for m in ["cyclo", "npath", "apc"]
                                                        for lang in SOURCES]
    print(data.sort_values("expert_mean_rank")[cols].to_string(index=False))
    print(corr.to_string(index=False))


if __name__ == "__main__":
    main()
