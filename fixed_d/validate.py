from __future__ import annotations

from dmpbench.algorithms import ALGORITHMS
from dmpbench.fixtures import FIXTURES
from dmpbench.oracle import exhaustive_oracle
from dmpbench.generators import demand_levels, random_directed_network


def main():
    for fixture, (net, d, expected) in FIXTURES.items():
        oracle = set(exhaustive_oracle(net, d))
        if expected is not None and oracle != set(expected):
            raise AssertionError(f"fixture transcription error for {fixture}: oracle={oracle}, expected={expected}")
        print(f"{fixture}: oracle has {len(oracle)} d-MPs")
        for name, fn in ALGORITHMS.items():
            got = set(fn(net, d).vectors)
            if got != oracle:
                raise AssertionError(f"{fixture}/{name}: missing={oracle-got}, extra={got-oracle}")
            print(f"  {name}: OK")
    print("randomized differential checks")
    for acyclic in (True, False):
        for seed in range(10):
            net = random_directed_network(5, 6 if acyclic else 8, 1, 2, seed, acyclic)
            for d in demand_levels(net, (0.33, 0.67)):
                oracle = set(exhaustive_oracle(net, d))
                for name, fn in ALGORITHMS.items():
                    got = set(fn(net, d).vectors)
                    if got != oracle:
                        raise AssertionError(
                            f"random/{acyclic=}/{seed=}/d={d}/{name}: "
                            f"missing={oracle-got}, extra={got-oracle}")
    print("  20 random networks: OK")
    print("all validations passed")


if __name__ == "__main__": main()

