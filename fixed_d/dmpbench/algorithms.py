from __future__ import annotations

from dataclasses import dataclass, field
import json
from time import perf_counter
from typing import Callable, Iterable, Sequence
from collections import defaultdict, deque

from .model import (Network, enumerate_simple_paths, feasible_exact_flow,
                    has_directed_cycle, is_dmp, max_flow, minimal_vectors,
                    output_digest)


PHASES = ("pre", "search", "map", "dup", "verify", "output")


@dataclass
class AlgorithmResult:
    algorithm: str
    vectors: list[tuple[int, ...]]
    times: dict[str, float]
    counters: dict[str, int | float | str] = field(default_factory=dict)

    def finalize(self) -> "AlgorithmResult":
        self.vectors = sorted(set(self.vectors))
        self.counters["output_count"] = len(self.vectors)
        self.counters["output_digest"] = output_digest(self.vectors)
        self.times["total"] = sum(self.times.get(p, 0.0) for p in PHASES)
        return self


class Clock:
    def __init__(self): self.t = {p: 0.0 for p in PHASES}
    def run(self, phase: str, fn: Callable, *args, **kwargs):
        a = perf_counter()
        try: return fn(*args, **kwargs)
        finally: self.t[phase] += perf_counter() - a


def _path_caps(net: Network, paths: Sequence[Sequence[int]]) -> list[int]:
    return [min(net.edges[i].capacity for i in p) for p in paths]


def _record_path_stats(ctr: dict[str, int | float | str], net: Network,
                       paths: Sequence[Sequence[int]]) -> None:
    lengths = [len(p) for p in paths]
    overlap = [sum(ei in p for p in paths) for ei in range(len(net.edges))]
    ctr.update(
        binary_paths=len(paths),
        path_arc_incidences=sum(lengths),
        mean_path_length=(sum(lengths) / len(lengths) if lengths else 0.0),
        max_path_length=max(lengths, default=0),
        max_arc_path_overlap=max(overlap, default=0),
        mean_arc_path_overlap=(sum(overlap) / len(overlap) if overlap else 0.0),
    )


def _enumerate_path_flows(net: Network, paths: Sequence[Sequence[int]], demand: int,
                          path_caps: Sequence[int], lower_load: Sequence[int] | None = None,
                          group_targets: Sequence[tuple[Sequence[int], int]] | None = None):
    """Yield (path-flow, induced arc-load), with early arc-capacity pruning."""
    h, m = len(paths), len(net.edges)
    loads = [0] * m; f = [0] * h
    membership = [tuple(p) for p in paths]
    target_for = [-1] * h
    remaining_group: list[int] = []
    if group_targets is not None:
        remaining_group = [int(b) for _, b in group_targets]
        for gi, (indices, _) in enumerate(group_targets):
            for j in indices: target_for[j] = gi
    suffix_cap = [0] * (h + 1)
    for j in range(h - 1, -1, -1): suffix_cap[j] = suffix_cap[j + 1] + path_caps[j]
    def rec(j: int, rem: int):
        if j == h:
            if rem == 0 and (not remaining_group or all(z == 0 for z in remaining_group)):
                if lower_load is None or all(a >= b for a, b in zip(loads, lower_load)):
                    yield tuple(f), tuple(loads)
            return
        if rem < 0 or rem > suffix_cap[j]: return
        gi = target_for[j]
        hi = min(path_caps[j], rem, remaining_group[gi] if gi >= 0 else rem)
        for value in range(hi + 1):
            ok = True
            for ei in membership[j]:
                if loads[ei] + value > net.edges[ei].capacity:
                    ok = False; break
            if not ok: continue
            f[j] = value
            for ei in membership[j]: loads[ei] += value
            if gi >= 0: remaining_group[gi] -= value
            yield from rec(j + 1, rem - value)
            if gi >= 0: remaining_group[gi] += value
            for ei in membership[j]: loads[ei] -= value
        f[j] = 0
    yield from rec(0, demand)


def _map_path_flow(paths: Sequence[Sequence[int]], flow: Sequence[int], m: int) -> tuple[int, ...]:
    """Apply x_i=sum_j a_ij f_j as a separately timed pipeline stage."""
    x = [0] * m
    for j, value in enumerate(flow):
        if value:
            for ei in paths[j]: x[ei] += value
    return tuple(x)


def _materialize_output(vectors: Sequence[Sequence[int]]) -> tuple[str, int]:
    """Canonicalize and serialize output in memory; disk I/O is excluded."""
    ordered = sorted(set(map(tuple, vectors)))
    payload = json.dumps(ordered, separators=(",", ":")).encode("utf-8")
    return output_digest(ordered), len(payload)


def lin_1995(net: Network, demand: int, max_paths: int | None = None) -> AlgorithmResult:
    """Lin--Jane--Yuan: MP-flow candidates followed by minimal filtering."""
    c = Clock(); ctr: dict[str, int | float | str] = {}
    a = perf_counter(); paths = c.run("pre", enumerate_simple_paths, net, max_paths)
    ctr["T_mp_generation"] = perf_counter() - a
    caps = c.run("pre", _path_caps, net, paths)
    _record_path_stats(ctr, net, paths)
    path_flows: list[tuple[int, ...]] = []
    def search():
        for f, _ in _enumerate_path_flows(net, paths, demand, caps):
            ctr["raw_path_flows"] = int(ctr.get("raw_path_flows", 0)) + 1
            path_flows.append(f)
    c.run("search", search)
    mapped = c.run("map", lambda: [_map_path_flow(paths, f, len(net.edges)) for f in path_flows])
    unique = c.run("dup", lambda: list(set(mapped)))
    ctr["raw_candidates"] = len(mapped); ctr["distinct_candidates"] = len(unique)
    vectors = c.run("verify", minimal_vectors, unique)
    ctr["duplicate_candidates_removed"] = len(mapped) - len(unique)
    ctr["minimality_rejections"] = len(unique) - len(vectors)
    digest, nbytes = c.run("output", _materialize_output, vectors)
    ctr.update(output_digest_timed=digest, output_bytes=nbytes)
    return AlgorithmResult("lin_1995", vectors, c.t, ctr).finalize()


def forghani_bonani_2017(net: Network, demand: int,
                          max_paths: int | None = None) -> AlgorithmResult:
    """Algorithm 2: lower bounds, Algorithm 1, hash deduplication, cycle test."""
    c = Clock(); ctr: dict[str, int | float | str] = {}
    a = perf_counter(); paths = c.run("pre", enumerate_simple_paths, net, max_paths)
    ctr["T_mp_generation"] = perf_counter() - a
    caps = c.run("pre", _path_caps, net, paths)
    def make_lower():
        M = list(net.capacities); out = []
        for i, mi in enumerate(M):
            y = M.copy(); y[i] = 0
            out.append(max(0, demand - max_flow(net, y, demand)))
        return tuple(out)
    lower = c.run("pre", make_lower)
    _record_path_stats(ctr, net, paths)
    ctr["positive_lower_bounds"] = sum(v > 0 for v in lower)
    ctr["max_flow_calls"] = len(net.edges)
    path_flows: list[tuple[int, ...]] = []
    def search():
        for f, _ in _enumerate_path_flows(net, paths, demand, caps, lower):
            ctr["raw_path_flows"] = int(ctr.get("raw_path_flows", 0)) + 1
            path_flows.append(f)
    c.run("search", search)
    mapped = c.run("map", lambda: [_map_path_flow(paths, f, len(net.edges)) for f in path_flows])
    unique = c.run("dup", lambda: list(dict.fromkeys(mapped)))
    ctr["raw_candidates"] = len(mapped); ctr["distinct_candidates"] = len(unique)
    def verify():
        ans = []
        for x in unique:
            if not has_directed_cycle(net, x): ans.append(x)
            else: ctr["cycle_rejections"] = int(ctr.get("cycle_rejections", 0)) + 1
        return ans
    vectors = c.run("verify", verify)
    ctr["duplicate_candidates_removed"] = len(mapped) - len(unique)
    ctr["minimality_rejections"] = len(unique) - len(vectors)
    digest, nbytes = c.run("output", _materialize_output, vectors)
    ctr.update(output_digest_timed=digest, output_bytes=nbytes)
    return AlgorithmResult("forghani_bonani_2017", vectors, c.t, ctr).finalize()


def _binding_groups(net: Network, paths: Sequence[Sequence[int]], path_caps: Sequence[int]):
    unbound = set(range(len(paths))); tau = set(range(len(net.edges)))
    groups: list[list[int]] = []; bounds: list[int] = []
    residual_group_added = False
    while unbound:
        viable = []
        for ei in tau:
            count = sum(ei in paths[j] for j in unbound)
            if count: viable.append((net.edges[ei].capacity, -count, ei))
        if not viable:
            group = sorted(unbound); groups.append(group)
            bounds.append(sum(path_caps[j] for j in group)); residual_group_added = True; break
        _, _, selected = min(viable)
        group = sorted(j for j in unbound if selected in paths[j])
        groups.append(group)
        bounds.append(min(sum(path_caps[j] for j in group), net.edges[selected].capacity))
        unbound.difference_update(group)
        covered_arcs = {ei for j in group for ei in paths[j]}
        tau.difference_update(covered_arcs)
    # In Huang et al.'s notation beta is deliberately not updated when the
    # residual B_k is created in Steps 1.8--1.10. Hence |beta| != m and the
    # final comparison must be global in precisely this case.
    return groups, bounds, not residual_group_added


def _bounded_compositions(total: int, bounds: Sequence[int]):
    x = [0] * len(bounds)
    def rec(i: int, rem: int):
        if i == len(bounds):
            if rem == 0: yield tuple(x)
            return
        for v in range(min(bounds[i], rem) + 1):
            x[i] = v; yield from rec(i + 1, rem - v)
    yield from rec(0, total)


def huang_2020(net: Network, demand: int, max_paths: int | None = None) -> AlgorithmResult:
    """Binding LBP algorithm (2020 final issue; 2019 early access)."""
    c = Clock(); ctr: dict[str, int | float | str] = {}
    a = perf_counter(); paths = c.run("pre", enumerate_simple_paths, net, max_paths)
    ctr["T_mp_generation"] = perf_counter() - a
    caps = c.run("pre", _path_caps, net, paths)
    groups, bounds, beta_complete = c.run("pre", _binding_groups, net, paths, caps)
    bflows = c.run("search", lambda: list(_bounded_compositions(demand, bounds)))
    _record_path_stats(ctr, net, paths)
    ctr.update(binding_groups=len(groups), binding_flow_vectors=len(bflows),
               beta_complete=int(beta_complete))
    group_minima: list[tuple[int, ...]] = []
    all_candidates: list[tuple[int, ...]] = []
    raw_count = 0
    for b in bflows:
        targets = [(groups[i], b[i]) for i in range(len(groups))]
        rows: list[tuple[int, ...]] = []
        def search_one():
            nonlocal raw_count
            for f, _ in _enumerate_path_flows(net, paths, demand, caps, group_targets=targets):
                raw_count += 1; rows.append(f)
        c.run("search", search_one)
        mapped = c.run("map", lambda: [_map_path_flow(paths, f, len(net.edges)) for f in rows])
        unique = c.run("dup", lambda: list(set(mapped)))
        all_candidates.extend(unique)
        # Theorem 2 permits comparison within each binding-flow group only
        # when the selected binding groups already cover every MP.
        if beta_complete:
            group_minima.extend(c.run("verify", minimal_vectors, unique))
    ctr["raw_path_flows"] = raw_count
    distinct_all = set(group_minima if beta_complete else all_candidates)
    ctr["distinct_group_candidates"] = len(distinct_all)
    vectors = (sorted(set(group_minima)) if beta_complete
               else c.run("verify", minimal_vectors, all_candidates))
    ctr["duplicate_candidates_removed"] = raw_count - len(distinct_all)
    ctr["minimality_rejections"] = len(distinct_all) - len(vectors)
    digest, nbytes = c.run("output", _materialize_output, vectors)
    ctr.update(output_digest_timed=digest, output_bytes=nbytes)
    return AlgorithmResult("huang_2020", vectors, c.t, ctr).finalize()


def _boundary_boxes(net: Network, lower: Sequence[int], upper: Sequence[int], demand: int):
    out_idx = [i for i, e in enumerate(net.edges) if e.u == net.source]
    in_idx = [i for i, e in enumerate(net.edges) if e.v == net.sink]
    def assignments(indices):
        vals = [0] * len(indices)
        def rec(k, rem):
            if k == len(indices):
                if rem == 0: yield tuple(vals)
                return
            ei = indices[k]
            for z in range(lower[ei], min(upper[ei], rem) + 1):
                vals[k] = z; yield from rec(k + 1, rem - z)
        yield from rec(0, demand)
    seen = set()
    for a in assignments(out_idx):
        for b in assignments(in_idx):
            lo, hi = list(lower), list(upper); ok = True
            fixed = {}
            for ei, z in zip(out_idx, a): fixed[ei] = z
            for ei, z in zip(in_idx, b):
                if ei in fixed and fixed[ei] != z: ok = False
                fixed[ei] = z
            if not ok: continue
            for ei, z in fixed.items(): lo[ei] = hi[ei] = z
            key = (tuple(lo), tuple(hi))
            if key not in seen: seen.add(key); yield key


def niu_2020(net: Network, demand: int, max_paths: int | None = None) -> AlgorithmResult:
    """Feasible-circulation and disjoint-box partition algorithm."""
    del max_paths
    c = Clock(); ctr: dict[str, int | float | str] = {}
    def prep():
        M = list(net.capacities); L = []
        for i in range(len(M)):
            y = M.copy(); y[i] = 0
            L.append(max(0, demand - max_flow(net, y, demand)))
        U = [min(w, demand) for w in M]
        return tuple(L), tuple(U)
    L, U = c.run("pre", prep)
    boxes = c.run("pre", lambda: list(_boundary_boxes(net, L, U, demand)))
    ctr["initial_boxes"] = len(boxes); ctr["positive_lower_bounds"] = sum(z > 0 for z in L)
    ctr["max_flow_calls"] = len(net.edges)
    vectors: list[tuple[int, ...]] = []
    stack = list(reversed(boxes))
    def search():
        while stack:
            lo, hi = stack.pop(); ctr["boxes_examined"] = int(ctr.get("boxes_examined", 0)) + 1
            ctr["max_flow_calls"] = int(ctr.get("max_flow_calls", 0)) + 1
            if max_flow(net, hi, demand) < demand:
                ctr["boxes_pruned_upper"] = int(ctr.get("boxes_pruned_upper", 0)) + 1; continue
            ctr["max_flow_calls"] = int(ctr.get("max_flow_calls", 0)) + 1
            if max_flow(net, lo, demand) == demand:
                ctr["lower_tests"] = int(ctr.get("lower_tests", 0)) + 1
                a = perf_counter()
                ctr["max_flow_calls"] = int(ctr.get("max_flow_calls", 0)) + 1
                valid = max_flow(net, lo, demand + 1) >= demand
                if valid:
                    for i, value in enumerate(lo):
                        if not value: continue
                        y = list(lo); y[i] -= 1
                        ctr["max_flow_calls"] = int(ctr.get("max_flow_calls", 0)) + 1
                        if max_flow(net, y, demand) >= demand:
                            valid = False; break
                c.t["verify"] += perf_counter() - a
                if valid: vectors.append(tuple(lo))
                continue
            f = feasible_exact_flow(net, lo, hi, demand)
            ctr["circulation_tests"] = int(ctr.get("circulation_tests", 0)) + 1
            if f is None: continue
            ctr["d_flows"] = int(ctr.get("d_flows", 0)) + 1
            a = perf_counter()
            if not has_directed_cycle(net, f): vectors.append(f)
            else: ctr["cycle_rejections"] = int(ctr.get("cycle_rejections", 0)) + 1
            c.t["verify"] += perf_counter() - a
            pivots = [i for i in range(len(f)) if lo[i] < f[i]]
            for pos, ei in enumerate(pivots):
                clo, chi = list(lo), list(hi)
                for pj in pivots[:pos]: clo[pj] = f[pj]
                chi[ei] = f[ei] - 1
                if clo[ei] <= chi[ei]: stack.append((tuple(clo), tuple(chi)))
    c.run("search", search)
    # Verification is invoked during the box traversal because its outcome
    # controls partitioning, but it is reported as a separate pipeline phase.
    # Remove that nested interval from search so T_total has no double count.
    c.t["search"] -= c.t["verify"]
    mapped = c.run("map", lambda: list(vectors))
    unique = c.run("dup", lambda: sorted(set(mapped)))
    ctr["duplicate_candidates_removed"] = len(mapped) - len(unique)
    digest, nbytes = c.run("output", _materialize_output, unique)
    ctr.update(output_digest_timed=digest, output_bytes=nbytes)
    return AlgorithmResult("niu_2020", unique, c.t, ctr).finalize()


def _bfs_edge_order(net: Network) -> list[int]:
    und = [[] for _ in range(net.n)]
    for i, e in enumerate(net.edges):
        und[e.u].append((e.v, i)); und[e.v].append((e.u, i))
    dist = [10**9] * net.n; dist[net.source] = 0; q = deque([net.source])
    while q:
        u = q.popleft()
        for v, _ in und[u]:
            if dist[v] == 10**9: dist[v] = dist[u] + 1; q.append(v)
    return sorted(range(len(net.edges)), key=lambda i: (min(dist[net.edges[i].u], dist[net.edges[i].v]),
                                                         max(dist[net.edges[i].u], dist[net.edges[i].v]), i))


def wu_2025(net: Network, demand: int, max_paths: int | None = None) -> AlgorithmResult:
    """Frontier-state d-flow decomposition and compressed DAG materialization."""
    del max_paths
    c = Clock(); ctr: dict[str, int | float | str] = {}
    order = c.run("pre", _bfs_edge_order, net)
    m = len(order)
    last = [-1] * net.n
    for level, ei in enumerate(order):
        e = net.edges[ei]; last[e.u] = last[e.v] = level
    # layer maps state -> node id; arcs store (next id, chosen capacity)
    next_id = 1
    start_bal = [0] * net.n; start_bal[net.source] = demand
    layer = {tuple(start_bal): 0}; dag: dict[int, list[tuple[int, int]]] = defaultdict(list)
    node_state = {0: tuple(start_bal)}
    def build():
        nonlocal layer, next_id
        for level, ei in enumerate(order):
            e = net.edges[ei]; new_layer = {}; state_to_id = {}
            for state, sid in layer.items():
                forced = None
                if last[e.u] == level: forced = state[e.u]
                values = [forced] if forced is not None else range(e.capacity + 1)
                for z in values:
                    if z is None or z < 0 or z > e.capacity: continue
                    b = list(state); b[e.u] -= z; b[e.v] += z
                    ok = True
                    for v in (e.u, e.v):
                        if last[v] == level:
                            target = demand if v == net.sink else 0
                            if b[v] != target: ok = False
                    if not ok: continue
                    key = tuple(b)
                    if key not in state_to_id:
                        state_to_id[key] = next_id; node_state[next_id] = key; next_id += 1
                    nid = state_to_id[key]; new_layer[key] = nid; dag[sid].append((nid, int(z)))
            layer = new_layer
            ctr["dd_peak_width"] = max(int(ctr.get("dd_peak_width", 0)), len(layer))
        ctr["dd_nodes"] = next_id; ctr["dd_arcs"] = sum(map(len, dag.values()))
    c.run("search", build)
    terminal = None
    expected = [0] * net.n; expected[int(net.sink)] = demand
    if tuple(expected) in layer: terminal = layer[tuple(expected)]
    assignments: list[tuple[int, ...]] = []
    if terminal is not None:
        rev_order = [0] * m; current = [0] * m
        def dfs(level: int, sid: int):
            if level == m:
                if sid == terminal:
                    for k, ei in enumerate(order): rev_order[ei] = current[k]
                    assignments.append(tuple(rev_order))
                return
            for nid, z in dag.get(sid, ()):
                current[level] = z; dfs(level + 1, nid)
        c.run("map", dfs, 0, 0)
    ctr["d_flow_candidates"] = len(assignments)
    unique = c.run("dup", lambda: list(set(assignments)))
    def verify():
        ans = []
        for x in unique:
            if not has_directed_cycle(net, x): ans.append(x)
            else: ctr["cycle_rejections"] = int(ctr.get("cycle_rejections", 0)) + 1
        return ans
    vectors = c.run("verify", verify)
    digest, nbytes = c.run("output", _materialize_output, vectors)
    ctr.update(output_digest_timed=digest, output_bytes=nbytes)
    return AlgorithmResult("wu_2025", vectors, c.t, ctr).finalize()


ALGORITHMS = {
    "lin_1995": lin_1995,
    "forghani_bonani_2017": forghani_bonani_2017,
    "huang_2020": huang_2020,
    "niu_2020": niu_2020,
    "wu_2025": wu_2025,
}
