"""One isolated peak-memory execution; timing results are intentionally discarded."""
from __future__ import annotations

import argparse
import json
import tracemalloc
from time import perf_counter

from dmpbench.algorithms import ALGORITHMS
from dmpbench.generators import load_instance
from dmpbench.model import is_dmp, output_digest


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("instance"); p.add_argument("algorithm", choices=sorted(ALGORITHMS))
    p.add_argument("--max-paths", type=int, default=1_000_000)
    a = p.parse_args(); net, demand = load_instance(a.instance)
    tracemalloc.start(); started = perf_counter()
    result = ALGORITHMS[a.algorithm](net, demand, max_paths=a.max_paths)
    memory_wall = perf_counter() - started
    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
    bad = [x for x in result.vectors if not is_dmp(net, x, demand)]
    if bad: raise AssertionError(f"{a.algorithm} returned {len(bad)} invalid vectors")
    print(json.dumps({"instance": net.name, "n": net.n, "m": len(net.edges),
                      "demand": demand, "algorithm": a.algorithm,
                      "peak_memory_bytes": peak, "memory_wall_seconds": memory_wall,
                      "output_count": len(result.vectors),
                      "output_digest": output_digest(result.vectors)}, sort_keys=True))


if __name__ == "__main__": main()
