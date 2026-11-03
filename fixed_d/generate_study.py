"""Generate a preregistered random fixed-demand study manifest."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dmpbench.generators import demand_records, random_directed_network, save_instance


def ints(text: str) -> list[int]:
    return [int(x) for x in text.split(",") if x]


def floats(text: str) -> list[float]:
    return [float(x) for x in text.split(",") if x]


def main() -> None:
    p = argparse.ArgumentParser(description="Create random directed MFN instances")
    p.add_argument("--nodes", default="6,8,10")
    p.add_argument("--density", default="2,3", help="m multiplier: m=density*n")
    p.add_argument("--seeds", default="0,1,2,3,4")
    p.add_argument("--fractions", default="0.25,0.50,0.75")
    p.add_argument("--capacity-low", type=int, default=1)
    p.add_argument("--capacity-high", type=int, default=5)
    p.add_argument("--families", choices=("both", "dag", "cyclic"), default="both")
    p.add_argument("--output-dir", default="study/random")
    a = p.parse_args()
    out = Path(a.output_dir); inst = out / "instances"; inst.mkdir(parents=True, exist_ok=True)
    families = [True, False] if a.families == "both" else [a.families == "dag"]
    records = []
    for n in ints(a.nodes):
        for mult in ints(a.density):
            for seed in ints(a.seeds):
                for acyclic in families:
                    try:
                        net = random_directed_network(n, mult*n, a.capacity_low,
                                                      a.capacity_high, seed, acyclic)
                    except ValueError:
                        continue
                    for drec in demand_records(net, floats(a.fractions)):
                        demand = drec["demand"]
                        filename = f"{net.name}_d{demand}.json"
                        meta = {"benchmark_block": "random", "family": "dag" if acyclic else "cyclic",
                                "seed": seed, "capacity_low": a.capacity_low,
                                "capacity_high": a.capacity_high, **drec}
                        save_instance(net, demand, inst / filename, meta)
                        records.append({"path": str((inst / filename).resolve()),
                                        "family": "dag" if acyclic else "cyclic",
                                        "seed": seed, **drec})
    manifest = {"schema": 2, "generator": vars(a), "instances": records}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} instances to {out / 'manifest.json'}")


if __name__ == "__main__":
    main()
