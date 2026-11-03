"""Create the preregistered published-example and held-out random main corpus."""
from __future__ import annotations

import json
from pathlib import Path

from dmpbench.fixtures import FIXTURES
from dmpbench.generators import demand_records, random_directed_network, save_instance

NODES = (7, 8)
SEEDS = (20, 21, 22, 23, 24)
FRACTIONS = (0.25, 0.50, 0.75)
CAPACITY_LOW, CAPACITY_HIGH = 3, 7
DENSITY_MULTIPLIER = 2


def main() -> None:
    root = Path("study/final_base"); inst = root / "instances"; inst.mkdir(parents=True, exist_ok=True)
    records = []
    for key, (net, demand, _) in FIXTURES.items():
        path = inst / f"published_{key}_d{demand}.json"
        meta = {"benchmark_block": "published_or_validation_example", "family": "published_example",
                "source_fixture": key, "demand": demand}
        save_instance(net, demand, path, meta)
        records.append({"path": str(path.resolve()), **meta})
    for n in NODES:
        for seed in SEEDS:
            for acyclic in (True, False):
                net = random_directed_network(n, DENSITY_MULTIPLIER*n, CAPACITY_LOW,
                                              CAPACITY_HIGH, seed, acyclic)
                for drec in demand_records(net, FRACTIONS):
                    path = inst / f"{net.name}_d{drec['demand']}.json"
                    meta = {"benchmark_block": "held_out_random",
                            "family": "dag" if acyclic else "cyclic", "seed": seed,
                            "capacity_low": CAPACITY_LOW, "capacity_high": CAPACITY_HIGH, **drec}
                    save_instance(net, drec["demand"], path, meta)
                    records.append({"path": str(path.resolve()), **meta})
    design = {
        "schema": 2, "study": "fixed-d final base corpus",
        "preregistered_after_calibration": True,
        "calibration_seeds_excluded": [0, 1, 2, 10, 11, 12],
        "random_design": {"nodes": list(NODES), "arcs": "2*n", "seeds": list(SEEDS),
                          "families": ["dag", "cyclic"], "capacity_range": [CAPACITY_LOW, CAPACITY_HIGH],
                          "target_demand_fractions": list(FRACTIONS),
                          "inclusion_rule": "retain every generated feasible case"},
        "instances": records,
    }
    (root / "manifest.json").write_text(json.dumps(design, indent=2), encoding="utf-8")
    (root / "study_design.json").write_text(json.dumps({k: v for k, v in design.items() if k != "instances"}, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} base cases to {root / 'manifest.json'}")


if __name__ == "__main__": main()
