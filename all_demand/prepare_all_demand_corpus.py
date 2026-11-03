"""Create the 37-network all-demand corpus used by the final study."""
from __future__ import annotations

import json
from pathlib import Path

from dmpbench.fixtures import FIXTURES
from dmpbench.generators import random_directed_network, save_instance, sndlib_derived
from prepare_sndlib_suite import find_topology, terminal_pairs


NODES = (7, 8)
SEEDS = (20, 21, 22, 23, 24)
SNDLIB_SEEDS = (40, 41)
TOPOLOGIES = ("abilene", "polska", "nobel-us")


def add(records: list[dict], net, path: Path, metadata: dict) -> None:
    # The stored demand is a compatibility placeholder. All algorithms solve
    # every positive feasible demand and ignore this field.
    save_instance(net, 0, path, metadata)
    records.append({"path": str(path.resolve()), **metadata})


def main() -> None:
    root = Path("study/all_demand_final")
    inst = root / "instances"; inst.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    for key, (net, _demand, _expected) in FIXTURES.items():
        add(records, net, inst / f"published_{key}.json",
            {"benchmark_block": "published_or_validation_example",
             "family": "published_example", "source_fixture": key})
    for n in NODES:
        for seed in SEEDS:
            for acyclic in (True, False):
                net = random_directed_network(n, 2 * n, 3, 7, seed, acyclic)
                add(records, net, inst / f"{net.name}.json",
                    {"benchmark_block": "held_out_random",
                     "family": "dag" if acyclic else "cyclic", "seed": seed,
                     "capacity_low": 3, "capacity_high": 7})
    native = Path("sndlib_native")
    selections = []
    for topology in TOPOLOGIES:
        source_file = find_topology(native, topology)
        for label, source, sink, distance in terminal_pairs(source_file):
            selections.append({"topology": topology, "terminal_pair_label": label,
                               "source": source, "sink": sink,
                               "undirected_hop_distance": distance})
            for seed in SNDLIB_SEEDS:
                net = sndlib_derived(source_file, source, sink, seed, 1, 2, "bidirected")
                add(records, net, inst / f"{net.name}.json",
                    {"benchmark_block": "sndlib_derived", "family": "sndlib_derived",
                     "topology": topology, "terminal_pair_label": label,
                     "source_terminal": source, "sink_terminal": sink,
                     "undirected_hop_distance": distance,
                     "transformation": "bidirected", "capacity_seed": seed,
                     "capacity_low": 1, "capacity_high": 2})
    design = {
        "schema": 1,
        "study": "all-demand d-MP final comparison",
        "task": "explicitly enumerate every d-MP for every positive feasible demand",
        "selection_rule": "same underlying networks as fixed-d study, with demand-specific duplicates collapsed",
        "blocks": {"published": 5, "held_out_random": 20, "sndlib_derived": 12},
        "random_design": {"nodes": list(NODES), "arcs": "2*n", "seeds": list(SEEDS),
                          "families": ["dag", "cyclic"], "capacity_range": [3, 7]},
        "sndlib_design": {"topologies": list(TOPOLOGIES), "capacity_seeds": list(SNDLIB_SEEDS),
                          "capacity_range": [1, 2], "transformation": "bidirected",
                          "terminal_rule": "lexicographically first diameter pair and pair closest to median hop distance"},
        "instances": records,
    }
    (root / "manifest.json").write_text(json.dumps(design, indent=2), encoding="utf-8")
    (root / "terminal_selection.json").write_text(json.dumps(selections, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} distinct networks to {root / 'manifest.json'}")


if __name__ == "__main__": main()
