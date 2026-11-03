"""Create deterministic SNDlib-derived screening or held-out main cases."""
from __future__ import annotations

import argparse
import json
import statistics
from collections import deque
from pathlib import Path

from dmpbench.generators import demand_records, parse_sndlib_native, save_instance, sndlib_derived


def terminal_pairs(path: Path) -> list[tuple[str, str, str, int]]:
    nodes, links = parse_sndlib_native(path); adj = {v: set() for v in nodes}
    for a, b in links: adj[a].add(b); adj[b].add(a)
    rows = []
    for s in sorted(nodes):
        dist = {s: 0}; q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in dist: dist[v] = dist[u] + 1; q.append(v)
        for t in sorted(nodes):
            if s < t and t in dist: rows.append((s, t, dist[t]))
    if not rows: raise ValueError(f"no connected node pair in {path}")
    diameter = sorted(rows, key=lambda z: (-z[2], z[0], z[1]))[0]
    median_distance = statistics.median(z[2] for z in rows)
    middle = sorted((z for z in rows if z[:2] != diameter[:2]),
                    key=lambda z: (abs(z[2] - median_distance), z[0], z[1]))[0]
    return [("diameter", diameter[0], diameter[1], diameter[2]),
            ("middle_distance", middle[0], middle[1], middle[2])]


def find_topology(directory: Path, stem: str) -> Path:
    matches = [p for p in directory.rglob("*") if p.is_file() and p.stem.lower() == stem.lower()]
    if not matches: raise FileNotFoundError(f"cannot find native SNDlib file with stem {stem!r} under {directory}")
    return sorted(matches)[0]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True, help="directory containing official native SNDlib files")
    p.add_argument("--mode", choices=("screen", "main"), default="screen")
    p.add_argument("--topologies", default="abilene,polska,nobel-us")
    p.add_argument("--transformation", choices=("bidirected", "acyclic"), default="bidirected")
    p.add_argument("--capacity-low", type=int, default=3); p.add_argument("--capacity-high", type=int, default=7)
    p.add_argument("--output-dir")
    a = p.parse_args(); seeds = (30, 31) if a.mode == "screen" else (40, 41)
    root = Path(a.output_dir or f"study/sndlib_{a.mode}_{a.transformation}")
    inst = root / "instances"; inst.mkdir(parents=True, exist_ok=True)
    records, selections = [], []
    for topology in a.topologies.split(","):
        source_file = find_topology(Path(a.input_dir), topology.strip())
        for label, source, sink, hop_distance in terminal_pairs(source_file):
            selections.append({"topology": topology, "terminal_pair_label": label,
                               "source": source, "sink": sink, "undirected_hop_distance": hop_distance})
            for seed in seeds:
                net = sndlib_derived(source_file, source, sink, seed, a.capacity_low,
                                     a.capacity_high, a.transformation)
                for drec in demand_records(net, (0.25, 0.50, 0.75)):
                    path = inst / f"{net.name}_d{drec['demand']}.json"
                    meta = {"benchmark_block": f"sndlib_{a.mode}", "family": "sndlib_derived",
                            "topology": topology, "terminal_pair_label": label,
                            "source_terminal": source, "sink_terminal": sink,
                            "undirected_hop_distance": hop_distance, "transformation": a.transformation,
                            "capacity_seed": seed, "capacity_low": a.capacity_low,
                            "capacity_high": a.capacity_high, **drec}
                    save_instance(net, drec["demand"], path, meta)
                    records.append({"path": str(path.resolve()), **meta})
    manifest = {"schema": 2, "study": f"SNDlib-derived {a.mode}", "generator": vars(a),
                "capacity_seeds": list(seeds), "terminal_selection_rule":
                "lexicographically first diameter pair and pair closest to median hop distance",
                "instances": records}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (root / "terminal_selection.json").write_text(json.dumps(selections, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} SNDlib-derived cases to {root / 'manifest.json'}")


if __name__ == "__main__": main()
