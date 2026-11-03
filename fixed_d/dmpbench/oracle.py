from __future__ import annotations

from itertools import product

from .model import Network, is_dmp


def exhaustive_oracle(net: Network, demand: int,
                      max_states: int = 2_000_000) -> list[tuple[int, ...]]:
    count = 1
    for e in net.edges:
        count *= e.capacity + 1
    if count > max_states:
        raise RuntimeError(f"oracle state space {count:,} exceeds limit {max_states:,}")
    return [tuple(x) for x in product(*(range(e.capacity + 1) for e in net.edges))
            if is_dmp(net, x, demand)]

