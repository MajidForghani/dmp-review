from __future__ import annotations

import csv
import json
import platform
import os
import statistics
import sys
import tracemalloc
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

from .all_algorithms import ALGORITHMS, PHASES
from .model import Network, is_dmp, max_flow


def _network_features(net: Network, demand: int) -> dict:
    indeg = [0] * net.n
    adj = [[] for _ in range(net.n)]
    for e in net.edges:
        adj[e.u].append(e.v); indeg[e.v] += 1
    queue = [i for i, z in enumerate(indeg) if z == 0]; seen = 0
    while queue:
        u = queue.pop(); seen += 1
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0: queue.append(v)
    capacities = list(net.capacities)
    full_flow = max_flow(net)
    return {
        "network_acyclic": int(seen == net.n),
        "density_directed": (len(net.edges) / (net.n * (net.n - 1)) if net.n > 1 else 0.0),
        "capacity_min": min(capacities, default=0),
        "capacity_max": max(capacities, default=0),
        "capacity_mean": (sum(capacities) / len(capacities) if capacities else 0.0),
        "capacity_sum": sum(capacities),
        "maximum_flow": full_flow,
        "demand_fraction_actual": (demand / full_flow if full_flow else 0.0),
    }


def run_once(name: str, net: Network, demand: int, max_paths: int | None = None,
             profile_memory: bool = True):
    start = perf_counter()
    result = ALGORITHMS[name](net, demand, max_paths=max_paths)
    elapsed = perf_counter() - start
    result.counters["wall_total_external"] = elapsed
    if profile_memory:
        # A separate execution avoids contaminating phase times with
        # tracemalloc's allocation-tracking overhead.
        tracemalloc.start()
        memory_result = ALGORITHMS[name](net, demand, max_paths=max_paths)
        _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
        if set(memory_result.vectors) != set(result.vectors):
            raise AssertionError(f"{name}: timed and memory-profile outputs differ")
        result.counters["peak_memory_bytes"] = peak
    out_idx = [i for i, e in enumerate(net.edges) if e.u == net.source]
    bad = []
    for x in result.vectors:
        level = sum(x[i] for i in out_idx)
        if level < 1 or not is_dmp(net, x, level): bad.append(x)
    if bad: raise AssertionError(f"{name} returned {len(bad)} invalid vectors")
    return result


def compare(net: Network, demand: int, algorithms=None, max_paths=None, profile_memory=True):
    names = list(algorithms or ALGORITHMS)
    results = [run_once(n, net, demand, max_paths, profile_memory) for n in names]
    reference = set(results[0].vectors)
    disagreements = {r.algorithm: {"missing": len(reference-set(r.vectors)),
                                    "extra": len(set(r.vectors)-reference)}
                     for r in results if set(r.vectors) != reference}
    return results, disagreements


def result_row(net: Network, demand: int, run_id: int, result):
    row = {"instance": net.name, "n": net.n, "m": len(net.edges), "demand": "all",
           "algorithm": result.algorithm, "run_id": run_id}
    row.update({f"T_{p}": result.times.get(p, 0.0) for p in PHASES})
    row["T_total"] = result.times.get("total", 0.0)
    row.update(_network_features(net, max_flow(net)))
    row.update(result.counters)
    return row


def append_csv(path: str | Path, rows: list[dict]) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f: existing = list(csv.DictReader(f))
    fields = sorted({k for r in existing + rows for k in r})
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(existing + rows)


def environment_record() -> dict:
    record = {"python": sys.version, "platform": platform.platform(),
              "processor": platform.processor(), "machine": platform.machine(),
              "logical_cpus": os.cpu_count(),
              "implementation": platform.python_implementation()}
    try:
        import psutil
        record.update(physical_cpus=psutil.cpu_count(logical=False),
                      total_memory_bytes=psutil.virtual_memory().total)
    except ImportError:
        record.update(physical_cpus=None, total_memory_bytes=None)
    return record

