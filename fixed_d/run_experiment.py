from __future__ import annotations

import argparse
import json
from pathlib import Path

from dmpbench.algorithms import ALGORITHMS
from dmpbench.fixtures import FIXTURES
from dmpbench.generators import load_instance
from dmpbench.runner import append_csv, compare, environment_record, result_row


def main():
    p = argparse.ArgumentParser(description="Run the fixed-demand d-MP comparison")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--fixture", choices=sorted(FIXTURES))
    g.add_argument("--instance", help="JSON instance file")
    p.add_argument("--algorithms", nargs="+", choices=sorted(ALGORITHMS), default=list(ALGORITHMS))
    p.add_argument("--repetitions", type=int, default=1)
    p.add_argument("--max-paths", type=int, default=1_000_000)
    p.add_argument("--no-memory-profile", action="store_true",
                   help="skip the separate peak-memory execution")
    p.add_argument("--output", default="results/results.csv")
    args = p.parse_args()
    if args.fixture:
        net, demand, _ = FIXTURES[args.fixture]
    else:
        net, demand = load_instance(args.instance)
    all_rows = []
    # Rotate order to reduce systematic warm-up/order bias.
    for rep in range(args.repetitions):
        names = args.algorithms[rep % len(args.algorithms):] + args.algorithms[:rep % len(args.algorithms)]
        results, disagreements = compare(net, demand, names, args.max_paths,
                                         not args.no_memory_profile)
        if disagreements:
            Path(args.output).with_suffix(f".disagreement.{rep}.json").write_text(
                json.dumps(disagreements, indent=2), encoding="utf-8")
            raise SystemExit(f"output disagreement: {disagreements}")
        all_rows.extend(result_row(net, demand, rep, r) for r in results)
    append_csv(args.output, all_rows)
    env = Path(args.output).with_name("environment.json")
    env.write_text(json.dumps(environment_record(), indent=2), encoding="utf-8")
    print(f"wrote {len(all_rows)} rows to {args.output}")


if __name__ == "__main__": main()

