from __future__ import annotations

import json
import random
from pathlib import Path

from .model import Network, max_flow


def random_directed_network(n: int, m: int, cap_low: int, cap_high: int,
                            seed: int, acyclic: bool = False) -> Network:
    if n < 3 or m < n - 1:
        raise ValueError("need n>=3 and m>=n-1")
    rng = random.Random(seed)
    pairs: set[tuple[int, int]] = set()
    # Guaranteed source-to-sink backbone.
    order = list(range(1, n - 1)); rng.shuffle(order)
    chain = [0] + order + [n - 1]
    for u, v in zip(chain, chain[1:]): pairs.add((u, v))
    possible = []
    rank = {v: i for i, v in enumerate(chain)}
    for u in range(n):
        for v in range(n):
            if u == v or v == 0 or u == n - 1: continue
            if acyclic and rank[u] >= rank[v]: continue
            possible.append((u, v))
    rng.shuffle(possible)
    for uv in possible:
        if len(pairs) >= m: break
        pairs.add(uv)
    if len(pairs) < m:
        raise ValueError("requested too many arcs for constraints")
    edges = [(u, v, rng.randint(cap_low, cap_high)) for u, v in sorted(pairs)]
    return Network.from_tuples(
        n, edges, 0, n - 1,
        f"random_{'dag' if acyclic else 'cyclic'}_n{n}_m{m}_c{cap_low}-{cap_high}_s{seed}",
    )


def demand_levels(net: Network, fractions=(0.25, 0.5, 0.75)) -> list[int]:
    D = max_flow(net)
    return sorted({max(1, min(D, round(D * f))) for f in fractions}) if D else []


def demand_records(net: Network, fractions=(0.25, 0.5, 0.75)) -> list[dict]:
    """Return unique rounded demands with explicit target and actual fractions."""
    D = max_flow(net)
    if not D: return []
    labels = ("low", "middle", "high") if len(fractions) == 3 else tuple(f"level_{i+1}" for i in range(len(fractions)))
    by_demand: dict[int, dict] = {}
    for label, fraction in zip(labels, fractions):
        d = max(1, min(D, round(D * fraction)))
        record = by_demand.setdefault(d, {"demand": d, "target_fractions": [], "demand_labels": []})
        record["target_fractions"].append(float(fraction)); record["demand_labels"].append(label)
    for record in by_demand.values():
        record["maximum_flow"] = D
        record["actual_fraction"] = record["demand"] / D
        record["target_fraction"] = min(record["target_fractions"],
                                        key=lambda z: abs(z - record["actual_fraction"]))
        record["demand_label"] = "+".join(record["demand_labels"])
    return [by_demand[d] for d in sorted(by_demand)]


def parse_sndlib_native(path: str | Path) -> tuple[list[str], list[tuple[str, str]]]:
    """Read node IDs and physical links from an SNDlib native network file."""
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    section = None; nodes: list[str] = []; links: list[tuple[str, str]] = []
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line: continue
        if line.startswith("NODES"): section = "nodes"; continue
        if line.startswith("LINKS"): section = "links"; continue
        if line.startswith(("DEMANDS", "ADMISSIBLE_PATHS")): section = None; continue
        if line == ")": section = None; continue
        if section == "nodes": nodes.append(line.split()[0])
        elif section == "links":
            toks = line.replace("(", " ").replace(")", " ").split()
            if len(toks) >= 3: links.append((toks[1], toks[2]))
    return nodes, links


def sndlib_derived(path: str | Path, source_name: str, sink_name: str,
                   seed: int, cap_low: int = 1, cap_high: int = 5,
                   transformation: str = "bidirected") -> Network:
    nodes, links = parse_sndlib_native(path)
    idx = {v: i for i, v in enumerate(nodes)}
    if source_name not in idx or sink_name not in idx:
        raise ValueError("terminal name absent from topology")
    # Renumber to keep source=0 and sink=n-1, which simplifies reproducibility.
    middle = [v for v in nodes if v not in (source_name, sink_name)]
    ordered = [source_name] + sorted(middle) + [sink_name]
    ren = {v: i for i, v in enumerate(ordered)}
    rng = random.Random(seed); out = []
    if transformation == "bidirected":
        for a, b in links:
            c1, c2 = rng.randint(cap_low, cap_high), rng.randint(cap_low, cap_high)
            out.extend([(ren[a], ren[b], c1), (ren[b], ren[a], c2)])
    elif transformation == "acyclic":
        # Deterministic orientation by renumbered rank; source has rank 0 and sink n-1.
        for a, b in links:
            u, v = ren[a], ren[b]
            if u > v: u, v = v, u
            out.append((u, v, rng.randint(cap_low, cap_high)))
    else:
        raise ValueError("transformation must be bidirected or acyclic")
    out = [(u, v, c) for u, v, c in out if v != 0 and u != len(ordered)-1]
    return Network.from_tuples(len(ordered), out, 0, len(ordered)-1,
                               f"sndlib_{Path(path).stem}_{transformation}_{source_name}_{sink_name}_"
                               f"c{cap_low}-{cap_high}_s{seed}")


def save_instance(net: Network, demand: int, path: str | Path, metadata: dict | None = None) -> None:
    obj = {"name": net.name, "n": net.n, "source": net.source, "sink": net.sink,
           "demand": demand,
           "edges": [[e.u, e.v, e.capacity] for e in net.edges]}
    if metadata: obj["metadata"] = metadata
    Path(path).write_text(json.dumps(obj, indent=2), encoding="utf-8")


def load_instance(path: str | Path) -> tuple[Network, int]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    return Network.from_tuples(obj["n"], obj["edges"], obj.get("source", 0),
                               obj.get("sink"), obj.get("name", Path(path).stem)), int(obj["demand"])

