"""Isolated worker used by run_study.py; normally not invoked directly."""
from __future__ import annotations

import argparse
import json

from dmpbench.generators import load_instance
from dmpbench.runner import result_row, run_once


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("instance")
    p.add_argument("algorithm")
    p.add_argument("run_id", type=int)
    p.add_argument("--max-paths", type=int, default=1_000_000)
    p.add_argument("--no-memory-profile", action="store_true")
    a = p.parse_args()
    net, demand = load_instance(a.instance)
    result = run_once(a.algorithm, net, demand, a.max_paths,
                      profile_memory=not a.no_memory_profile)
    print(json.dumps(result_row(net, demand, a.run_id, result), sort_keys=True))


if __name__ == "__main__":
    main()
