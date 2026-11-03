from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from time import perf_counter
from typing import Callable, Sequence

from .algorithms import forghani_bonani_2017
from .model import Network, enumerate_simple_paths, has_directed_cycle, max_flow, output_digest


Vector = tuple[int, ...]
PHASES = ("pre", "search", "map", "dup", "verify", "output")


@dataclass
class AlgorithmResult:
    algorithm: str
    vectors: list[Vector]
    times: dict[str, float]
    counters: dict[str, int | float | str] = field(default_factory=dict)

    def finalize(self, net: Network) -> "AlgorithmResult":
        self.vectors = sorted(set(self.vectors))
        by_level: dict[int, int] = {}
        for x in self.vectors:
            d = sum(x[i] for i, e in enumerate(net.edges) if e.u == net.source)
            by_level[d] = by_level.get(d, 0) + 1
        self.counters["level_counts_json"] = json.dumps(by_level, sort_keys=True)
        self.counters["levels_returned"] = len(by_level)
        self.counters["output_count"] = len(self.vectors)
        self.counters["output_digest"] = output_digest(self.vectors)
        self.times["total"] = sum(self.times.get(p, 0.0) for p in PHASES)
        return self


class Clock:
    def __init__(self) -> None:
        self.t = {p: 0.0 for p in PHASES}

    def run(self, phase: str, fn: Callable, *args, **kwargs):
        started = perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            self.t[phase] += perf_counter() - started


def _path_vectors(net: Network, max_paths: int | None) -> list[Vector]:
    rows = []
    for path in enumerate_simple_paths(net, max_paths):
        x = [0] * len(net.edges)
        for i in path:
            x[i] = 1
        rows.append(tuple(x))
    return rows


def _support_acyclic(net: Network, x: Sequence[int]) -> bool:
    return not has_directed_cycle(net, x)


def _lambda_set(net: Network, x: Vector, paths: list[Vector]) -> frozenset[int]:
    return frozenset(j for j, p in enumerate(paths)
                     if any(x[k] + p[k] > net.edges[k].capacity for k in range(len(x))))


@dataclass(frozen=True)
class _BaiRecord:
    vector: Vector
    components: tuple[int, ...]
    infeasible_additions: frozenset[int]


@dataclass(frozen=True)
class _Yeh2018Record:
    """One sorted record in Yeh's (2018) addition-based construction."""

    vector: Vector
    log_prime_value: float
    infeasible_additions: frozenset[int]


def _merge_yeh2018(left: list[_Yeh2018Record], right: list[_Yeh2018Record]) -> tuple[list[_Yeh2018Record], int]:
    """Merge two L-sorted lists and suppress exact duplicate vectors.

    Yeh (2018) identifies duplicates through logarithmic prime values. Binary
    floating-point equality is not the prime-factor theorem, so tuple equality
    is the final equality test. The logarithmic value still supplies the
    published ordering and merge rule.
    """
    out: list[_Yeh2018Record] = []
    seen: set[Vector] = set()
    i = j = duplicates = 0
    while i < len(left) or j < len(right):
        if j >= len(right) or (i < len(left) and
                               (left[i].log_prime_value, left[i].vector) <=
                               (right[j].log_prime_value, right[j].vector)):
            item = left[i]; i += 1
        else:
            item = right[j]; j += 1
        if item.vector in seen:
            duplicates += 1
            continue
        seen.add(item.vector); out.append(item)
    return out, duplicates


def yeh_2018(net: Network, _demand: int = 0,
             max_paths: int | None = None) -> AlgorithmResult:
    """Yeh's (2018) addition-based algorithm for all possible demands.

    This follows Steps 0--2 and Lemmas 5--16 in W.-C. Yeh, IEEE Transactions
    on Reliability 67(1), 2018, 308--315. The apparent ``j`` typo in Step 1.5
    is interpreted as the outer path index ``i``. Exact tuple equality guards
    the logarithmic-prime duplicate test against floating-point roundoff.
    """
    c = Clock(); ctr: dict[str, int | float | str] = {}
    paths = c.run("pre", _path_vectors, net, max_paths)
    dmax = c.run("pre", max_flow, net)
    logs = c.run("pre", _prime_logs, len(net.edges))
    path_scores = c.run("pre", lambda: [sum(v * q for v, q in zip(p, logs))
                                         for p in paths])
    order = c.run("pre", lambda: sorted(range(len(paths)),
                                         key=lambda i: (path_scores[i], paths[i])))
    paths = [paths[i] for i in order]
    path_scores = [path_scores[i] for i in order]
    edge_users = c.run("pre", lambda: [frozenset(i for i, p in enumerate(paths) if p[k])
                                        for k in range(len(net.edges))])
    def saturated_additions(x: Vector) -> frozenset[int]:
        blocked: set[int] = set()
        for k, value in enumerate(x):
            if value == net.edges[k].capacity:
                blocked.update(edge_users[k])
        return frozenset(blocked)
    lambdas = c.run("pre", lambda: [saturated_additions(p) for p in paths])
    ctr.update(binary_paths=len(paths), maximum_flow=dmax, candidate_additions=0,
               lambda_prevented=0, cycle_pruned=0, merge_operations=0,
               duplicates_removed=0, exact_equality_safeguards=0)

    p1_records = [_Yeh2018Record(p, s, lambdas[i])
                  for i, (p, s) in enumerate(zip(paths, path_scores))]
    found: set[Vector] = set(paths)
    if dmax <= 1 or not paths:
        return AlgorithmResult("yeh_2018", sorted(found), c.t, ctr).finalize(net)

    previous: list[_Yeh2018Record] = []
    m = len(net.edges)
    for d in range(2, dmax + 1):
        current: list[_Yeh2018Record] = []
        for i, one in enumerate(p1_records):
            source_records = p1_records[i:] if d == 2 else previous
            delta: list[_Yeh2018Record] = []
            delta_seen: set[Vector] = set()
            for prior in source_records:
                if i in prior.infeasible_additions:
                    ctr["lambda_prevented"] += 1
                    continue
                started = perf_counter()
                x = tuple(prior.vector[k] + one.vector[k] for k in range(m))
                score = prior.log_prime_value + one.log_prime_value
                c.t["search"] += perf_counter() - started
                ctr["candidate_additions"] += 1
                started = perf_counter(); acyclic = _support_acyclic(net, x)
                c.t["verify"] += perf_counter() - started
                if not acyclic:
                    ctr["cycle_pruned"] += 1
                    continue
                started = perf_counter()
                if x in delta_seen:
                    ctr["duplicates_removed"] += 1
                    ctr["exact_equality_safeguards"] += 1
                    c.t["dup"] += perf_counter() - started
                    continue
                delta_seen.add(x)
                c.t["dup"] += perf_counter() - started
                # Lemma 10: inherit both Lambda sets and add E_k for every
                # newly saturated arc. Rechecking all paths is unnecessary.
                started = perf_counter()
                blocked = set(prior.infeasible_additions)
                blocked.update(one.infeasible_additions)
                for k, value in enumerate(x):
                    if value == net.edges[k].capacity:
                        blocked.update(edge_users[k])
                delta.append(_Yeh2018Record(x, score, frozenset(blocked)))
                c.t["verify"] += perf_counter() - started
            started = perf_counter()
            delta.sort(key=lambda r: (r.log_prime_value, r.vector))
            current, duplicates = _merge_yeh2018(current, delta)
            ctr["merge_operations"] += 1
            ctr["duplicates_removed"] += duplicates
            ctr["exact_equality_safeguards"] += duplicates
            c.t["dup"] += perf_counter() - started
        previous = current
        found.update(r.vector for r in current)
        if not previous:
            break

    def materialize():
        ordered = sorted(found)
        json.dumps(ordered, separators=(",", ":")).encode("utf-8")
        return ordered
    vectors = c.run("output", materialize)
    return AlgorithmResult("yeh_2018", vectors, c.t, ctr).finalize(net)


def bai_2021(net: Network, _demand: int = 0,
             max_paths: int | None = None) -> AlgorithmResult:
    """Independent reconstruction of Bai et al. (2021), Algorithms 1--2.

    The ordered binary-MP list is generated once.  The published Lambda, rho,
    nondecreasing-component, and cycle rules are applied in their prescribed
    order.  Exact tuples implement equality; no logarithmic fingerprint is
    trusted as an equality test.
    """
    c = Clock(); ctr: dict[str, int | float | str] = {}
    paths = c.run("pre", _path_vectors, net, max_paths)
    dmax = c.run("pre", max_flow, net)
    lambdas = c.run("pre", lambda: [_lambda_set(net, p, paths) for p in paths])
    ctr.update(binary_paths=len(paths), maximum_flow=dmax, candidate_additions=0,
               lambda_prevented=0, cycle_pruned=0, rho_pairs_recorded=0,
               rho_prevented=0, order_prevented=0, unexpected_duplicates=0)
    found: set[Vector] = set(paths)
    rho = [set() for _ in paths]
    records: list[_BaiRecord] = []
    first: set[Vector] = set()
    m = len(net.edges)
    for i in range(len(paths)):
        for j in range(i, len(paths)):
            if i in lambdas[j]:
                ctr["lambda_prevented"] += 1; continue
            started = perf_counter()
            x = tuple(paths[i][k] + paths[j][k] for k in range(m))
            c.t["search"] += perf_counter() - started
            ctr["candidate_additions"] += 1
            started = perf_counter(); acyclic = _support_acyclic(net, x)
            c.t["verify"] += perf_counter() - started
            if not acyclic:
                ctr["cycle_pruned"] += 1; continue
            started = perf_counter()
            if x in first:
                rho[i].add(j); ctr["rho_pairs_recorded"] += 1
                c.t["dup"] += perf_counter() - started; continue
            first.add(x); c.t["dup"] += perf_counter() - started
            records.append(_BaiRecord(x, (i, j), _lambda_set(net, x, paths)))
            found.add(x)
    for _level in range(3, dmax + 1):
        nxt: list[_BaiRecord] = []; seen: set[Vector] = set()
        for i, p in enumerate(paths):
            for previous in records:
                if min(previous.components) < i:
                    ctr["order_prevented"] += 1; continue
                if set(previous.components) & rho[i]:
                    ctr["rho_prevented"] += 1; continue
                if i in previous.infeasible_additions:
                    ctr["lambda_prevented"] += 1; continue
                started = perf_counter()
                x = tuple(p[k] + previous.vector[k] for k in range(m))
                c.t["search"] += perf_counter() - started
                ctr["candidate_additions"] += 1
                started = perf_counter(); acyclic = _support_acyclic(net, x)
                c.t["verify"] += perf_counter() - started
                if not acyclic:
                    ctr["cycle_pruned"] += 1; continue
                started = perf_counter()
                duplicate = x in seen
                if not duplicate: seen.add(x)
                c.t["dup"] += perf_counter() - started
                if duplicate:
                    ctr["unexpected_duplicates"] += 1; continue
                components = (i,) + previous.components
                nxt.append(_BaiRecord(x, components, _lambda_set(net, x, paths)))
                found.add(x)
        records = nxt
        if not records: break
    def materialize():
        ordered = sorted(found)
        json.dumps(ordered, separators=(",", ":")).encode("utf-8")
        return ordered
    vectors = c.run("output", materialize)
    return AlgorithmResult("bai_2021", vectors, c.t, ctr).finalize(net)


def repeated_forghani_bonani_2017(net: Network, _demand: int = 0,
                                  max_paths: int | None = None) -> AlgorithmResult:
    """Solve every d=1,...,dmax independently with the 2017 fixed-d method."""
    c = Clock(); ctr: dict[str, int | float | str] = {"fixed_d_calls": 0}
    started = perf_counter(); dmax = max_flow(net); c.t["pre"] += perf_counter() - started
    vectors: list[Vector] = []
    for d in range(1, dmax + 1):
        result = forghani_bonani_2017(net, d, max_paths=max_paths)
        ctr["fixed_d_calls"] += 1
        vectors.extend(result.vectors)
        for phase in PHASES:
            c.t[phase] += result.times.get(phase, 0.0)
        for key in ("raw_path_flows", "raw_candidates", "distinct_candidates",
                    "duplicate_candidates_removed", "cycle_rejections", "max_flow_calls"):
            ctr[key] = int(ctr.get(key, 0)) + int(result.counters.get(key, 0))
    ctr["maximum_flow"] = dmax
    return AlgorithmResult("repeated_fb_2017", vectors, c.t, ctr).finalize(net)


def _prime_logs(count: int) -> list[float]:
    primes: list[int] = []; value = 2
    while len(primes) < count:
        if all(value % p for p in primes if p * p <= value): primes.append(value)
        value += 1
    return [math.log(p) for p in primes]


def yeh_zuo_2019(net: Network, _demand: int = 0,
                  max_paths: int | None = None) -> AlgorithmResult:
    """Yeh--Zuo subtraction recurrence, including required seed construction.

    The paper assumes P1 and P_dmax are given.  For an end-to-end comparison,
    P1 is generated and P_dmax is obtained with the selected robust fixed-d
    solver.  Its complete cost is included in preprocessing and also exposed as
    ``T_seed_dmax``.  The subtraction recurrence itself is unchanged.
    """
    c = Clock(); ctr: dict[str, int | float | str] = {}
    paths = c.run("pre", _path_vectors, net, max_paths)
    dmax = c.run("pre", max_flow, net)
    logs = c.run("pre", _prime_logs, len(net.edges))
    if dmax <= 1:
        return AlgorithmResult("yeh_zuo_2019", paths, c.t,
                               {"binary_paths": len(paths), "maximum_flow": dmax,
                                "T_seed_dmax": 0.0, "subtraction_candidates": 0}).finalize(net)
    seed_started = perf_counter()
    seed = forghani_bonani_2017(net, dmax, max_paths=max_paths)
    seed_time = perf_counter() - seed_started
    c.t["pre"] += seed_time
    ctr.update(binary_paths=len(paths), maximum_flow=dmax, T_seed_dmax=seed_time,
               seed_dmax_count=len(seed.vectors), subtraction_pairs=0,
               dominance_prevented=0, subtraction_candidates=0,
               duplicates_removed=0)
    def score(x: Vector) -> float:
        return sum(v * q for v, q in zip(x, logs))
    p1 = c.run("dup", lambda: sorted(set(paths), key=lambda x: (score(x), x)))
    levels: dict[int, list[Vector]] = {1: p1, dmax: sorted(set(seed.vectors),
                                                          key=lambda x: (-score(x), x))}
    for d in range(dmax - 1, 1, -1):
        candidates: list[Vector] = []
        raw_at_level = 0
        for upper in levels[d + 1]:
            delta: list[Vector] = []
            for one in p1:
                ctr["subtraction_pairs"] += 1
                started = perf_counter(); dominated = all(a >= b for a, b in zip(upper, one))
                c.t["verify"] += perf_counter() - started
                if not dominated:
                    ctr["dominance_prevented"] += 1; continue
                started = perf_counter()
                delta.append(tuple(a - b for a, b in zip(upper, one)))
                c.t["search"] += perf_counter() - started
                ctr["subtraction_candidates"] += 1
                raw_at_level += 1
            started = perf_counter()
            candidates.extend(delta)
            candidates.sort(key=lambda x: (score(x), x))
            candidates = list(dict.fromkeys(candidates))
            c.t["dup"] += perf_counter() - started
        ctr["duplicates_removed"] += raw_at_level - len(set(candidates))
        levels[d] = candidates
    vectors = [x for d in sorted(levels) for x in levels[d]]
    def materialize():
        ordered = sorted(set(vectors))
        json.dumps(ordered, separators=(",", ":")).encode("utf-8")
        return ordered
    vectors = c.run("output", materialize)
    return AlgorithmResult("yeh_zuo_2019", vectors, c.t, ctr).finalize(net)


ALGORITHMS = {
    "repeated_fb_2017": repeated_forghani_bonani_2017,
    "yeh_2018": yeh_2018,
    "yeh_zuo_2019": yeh_zuo_2019,
    "bai_2021": bai_2021,
}
