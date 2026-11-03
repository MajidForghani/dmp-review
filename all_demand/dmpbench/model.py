from __future__ import annotations

from dataclasses import dataclass
from collections import deque
import hashlib
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Edge:
    u: int
    v: int
    capacity: int


@dataclass(frozen=True)
class Network:
    n: int
    edges: tuple[Edge, ...]
    source: int = 0
    sink: int | None = None
    name: str = "network"

    def __post_init__(self) -> None:
        if self.sink is None:
            object.__setattr__(self, "sink", self.n - 1)
        if not (0 <= self.source < self.n and 0 <= int(self.sink) < self.n):
            raise ValueError("invalid terminals")
        if self.source == self.sink:
            raise ValueError("source and sink must differ")
        for e in self.edges:
            if not (0 <= e.u < self.n and 0 <= e.v < self.n and e.u != e.v):
                raise ValueError(f"invalid edge {e}")
            if e.capacity < 0:
                raise ValueError("capacities must be nonnegative integers")

    @classmethod
    def from_tuples(cls, n: int, edges: Iterable[tuple[int, int, int]],
                    source: int = 0, sink: int | None = None,
                    name: str = "network") -> "Network":
        return cls(n, tuple(Edge(int(u), int(v), int(c)) for u, v, c in edges),
                   source, sink, name)

    @property
    def capacities(self) -> tuple[int, ...]:
        return tuple(e.capacity for e in self.edges)


class _Arc:
    __slots__ = ("to", "rev", "cap", "initial")
    def __init__(self, to: int, rev: int, cap: int):
        self.to, self.rev, self.cap, self.initial = to, rev, cap, cap


class Dinic:
    def __init__(self, n: int):
        self.n = n
        self.g: list[list[_Arc]] = [[] for _ in range(n)]

    def add_edge(self, u: int, v: int, cap: int) -> tuple[int, int]:
        a = _Arc(v, len(self.g[v]), int(cap))
        b = _Arc(u, len(self.g[u]), 0)
        self.g[u].append(a); self.g[v].append(b)
        return u, len(self.g[u]) - 1

    def flow(self, ref: tuple[int, int]) -> int:
        a = self.g[ref[0]][ref[1]]
        return a.initial - a.cap

    def max_flow(self, s: int, t: int, limit: int | None = None) -> int:
        total = 0
        inf = 10**30
        while limit is None or total < limit:
            level = [-1] * self.n
            level[s] = 0
            q = deque([s])
            while q:
                u = q.popleft()
                for a in self.g[u]:
                    if a.cap and level[a.to] < 0:
                        level[a.to] = level[u] + 1; q.append(a.to)
            if level[t] < 0:
                break
            it = [0] * self.n
            def dfs(u: int, f: int) -> int:
                if u == t:
                    return f
                while it[u] < len(self.g[u]):
                    a = self.g[u][it[u]]
                    if a.cap and level[a.to] == level[u] + 1:
                        z = dfs(a.to, min(f, a.cap))
                        if z:
                            a.cap -= z; self.g[a.to][a.rev].cap += z
                            return z
                    it[u] += 1
                return 0
            while limit is None or total < limit:
                z = dfs(s, inf if limit is None else limit - total)
                if not z:
                    break
                total += z
        return total


def max_flow(net: Network, capacities: Sequence[int] | None = None,
             limit: int | None = None) -> int:
    caps = net.capacities if capacities is None else capacities
    d = Dinic(net.n)
    for e, c in zip(net.edges, caps):
        if c > 0:
            d.add_edge(e.u, e.v, int(c))
    return d.max_flow(net.source, int(net.sink), limit)


def feasible_exact_flow(net: Network, lower: Sequence[int], upper: Sequence[int],
                        demand: int) -> tuple[int, ...] | None:
    """One integral s-t flow of exactly demand within component bounds."""
    n, ss, tt = net.n, net.n, net.n + 1
    din = Dinic(n + 2)
    balance = [0] * n
    refs: list[tuple[int, int]] = []
    for e, lo, hi in zip(net.edges, lower, upper):
        if lo > hi:
            return None
        refs.append(din.add_edge(e.u, e.v, int(hi - lo)))
        balance[e.u] -= int(lo); balance[e.v] += int(lo)
    # Fixed return arc t -> s closes an exact-d circulation.
    balance[int(net.sink)] -= demand
    balance[net.source] += demand
    required = 0
    for v, b in enumerate(balance):
        if b > 0:
            din.add_edge(ss, v, b); required += b
        elif b < 0:
            din.add_edge(v, tt, -b)
    if din.max_flow(ss, tt) != required:
        return None
    return tuple(int(lo) + din.flow(ref) for lo, ref in zip(lower, refs))


def enumerate_simple_paths(net: Network, max_paths: int | None = None) -> list[tuple[int, ...]]:
    adj: list[list[tuple[int, int]]] = [[] for _ in range(net.n)]
    for i, e in enumerate(net.edges):
        if e.capacity > 0:
            adj[e.u].append((e.v, i))
    for row in adj:
        row.sort(key=lambda z: (z[0], z[1]))
    out: list[tuple[int, ...]] = []
    seen = {net.source}
    path: list[int] = []
    def dfs(u: int) -> None:
        if u == net.sink:
            out.append(tuple(path))
            if max_paths is not None and len(out) > max_paths:
                raise RuntimeError(f"path limit {max_paths} exceeded")
            return
        for v, ei in adj[u]:
            if v not in seen:
                seen.add(v); path.append(ei); dfs(v); path.pop(); seen.remove(v)
    dfs(net.source)
    return out


def has_directed_cycle(net: Network, x: Sequence[int]) -> bool:
    adj = [[] for _ in range(net.n)]
    for e, c in zip(net.edges, x):
        if c > 0:
            adj[e.u].append(e.v)
    color = [0] * net.n
    def dfs(u: int) -> bool:
        color[u] = 1
        for v in adj[u]:
            if color[v] == 1 or (color[v] == 0 and dfs(v)):
                return True
        color[u] = 2
        return False
    return any(color[v] == 0 and dfs(v) for v in range(net.n))


def is_dmp(net: Network, x: Sequence[int], demand: int) -> bool:
    if max_flow(net, x, demand + 1) < demand:
        return False
    for i, value in enumerate(x):
        if value:
            y = list(x); y[i] -= 1
            if max_flow(net, y, demand) >= demand:
                return False
    return True


def minimal_vectors(vectors: Iterable[Sequence[int]]) -> list[tuple[int, ...]]:
    unique = sorted(set(tuple(map(int, x)) for x in vectors), key=lambda x: (sum(x), x))
    mins: list[tuple[int, ...]] = []
    for x in unique:
        if not any(all(a <= b for a, b in zip(y, x)) for y in mins):
            mins.append(x)
    return sorted(mins)


def output_digest(vectors: Iterable[Sequence[int]]) -> str:
    rows = sorted(tuple(map(int, x)) for x in vectors)
    raw = "\n".join(",".join(map(str, x)) for x in rows).encode()
    return hashlib.sha256(raw).hexdigest()

