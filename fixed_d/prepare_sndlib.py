"""Convert an official SNDlib native topology into explicit directed instances."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dmpbench.generators import demand_records, save_instance, sndlib_derived


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("native_file")
    p.add_argument("source")
    p.add_argument("sink")
    p.add_argument("--transformation", choices=("bidirected", "acyclic"), default="bidirected")
    p.add_argument("--seeds", default="0,1,2,3,4")
    p.add_argument("--fractions", default="0.25,0.50,0.75")
    p.add_argument("--capacity-low", type=int, default=1)
    p.add_argument("--capacity-high", type=int, default=5)
    p.add_argument("--output-dir", default="study/sndlib")
    a = p.parse_args()
    out = Path(a.output_dir); inst = out / "instances"; inst.mkdir(parents=True, exist_ok=True)
    records = []
    for seed in map(int, a.seeds.split(",")):
        net = sndlib_derived(a.native_file, a.source, a.sink, seed,
                             a.capacity_low, a.capacity_high, a.transformation)
        for drec in demand_records(net, tuple(map(float, a.fractions.split(",")))):
            demand = drec["demand"]
            path = inst / f"{net.name}_d{demand}.json"
            save_instance(net, demand, path, {"benchmark_block": "sndlib_custom", **drec})
            records.append({"path": str(path.resolve()), "family": "sndlib-derived",
                            "source_file": str(Path(a.native_file).resolve()),
                            "transformation": a.transformation, "seed": seed, **drec})
    manifest = {"schema": 2, "generator": vars(a), "instances": records}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} instances to {out / 'manifest.json'}")


if __name__ == "__main__":
    main()
