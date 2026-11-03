from __future__ import annotations

from dmpbench.all_algorithms import ALGORITHMS, bai_2021, yeh_2018, yeh_zuo_2019
from dmpbench.fixtures import FIXTURES
from dmpbench.generators import random_directed_network
from dmpbench.model import Network, max_flow, output_digest
from dmpbench.oracle import exhaustive_oracle


def oracle_all(net: Network):
    rows = []
    for d in range(1, max_flow(net) + 1): rows.extend(exhaustive_oracle(net, d))
    return sorted(set(rows))


def yeh_example() -> Network:
    return Network.from_tuples(4, [(0, 1, 3), (1, 3, 2), (1, 2, 1),
                                   (2, 1, 1), (0, 2, 1), (2, 3, 2)],
                               0, 3, "yeh_zuo_2019_fig1")


def bai_example() -> Network:
    return Network.from_tuples(6, [(0, 1, 2), (0, 2, 2), (1, 2, 1),
                                   (1, 3, 1), (2, 3, 2), (2, 4, 1),
                                   (3, 4, 1), (3, 5, 2), (4, 5, 2)],
                               0, 5, "bai_2021_example")


def check(net: Network, use_oracle: bool = True) -> bool:
    reference = oracle_all(net) if use_oracle else None
    results = {}
    for name, fn in ALGORITHMS.items():
        got = fn(net, 0, max_paths=1_000_000).vectors
        results[name] = got
        if reference is not None and name != "yeh_zuo_2019" and set(got) != set(reference):
            raise AssertionError(f"{net.name}/{name}: missing={set(reference)-set(got)}, extra={set(got)-set(reference)}")
    exact_digest = output_digest(results["repeated_fb_2017"])
    if output_digest(results["bai_2021"]) != exact_digest:
        raise AssertionError(f"exact-method disagreement on {net.name}")
    if output_digest(results["yeh_2018"]) != exact_digest:
        raise AssertionError(f"Yeh-2018 disagreement on {net.name}")
    yeh_complete = output_digest(results["yeh_zuo_2019"]) == exact_digest
    label = "complete" if yeh_complete else "literal Yeh--Zuo incomplete"
    print(f"{net.name}: {len(results['repeated_fb_2017'])} all-level vectors: exact methods OK; {label}")
    return yeh_complete


def main() -> None:
    # Yeh (2018), Fig. 1 and Tables II--VI: 4, 5, 3, and 1 vectors.
    # In particular, (1,2,0,1,1,0) must be present in P2.
    yeh = yeh_example(); yr = yeh_zuo_2019(yeh)
    y18 = yeh_2018(yeh)
    if y18.counters["level_counts_json"] != '{"1": 4, "2": 5, "3": 3, "4": 1}':
        raise AssertionError(f"Yeh-2018 example counts differ: {y18.counters['level_counts_json']}")
    if (1, 2, 0, 1, 1, 0) not in y18.vectors:
        raise AssertionError("Yeh-2018 Fig. 1 lost the documented fifth 2-MP")
    published_y18 = {
        (1, 1, 0, 0, 0, 0), (1, 0, 1, 0, 0, 1),
        (0, 1, 0, 1, 1, 0), (0, 0, 0, 0, 1, 1),
        (1, 2, 0, 1, 1, 0), (1, 0, 1, 0, 1, 2),
        (1, 1, 0, 0, 1, 1), (2, 1, 1, 0, 0, 1),
        (2, 2, 0, 0, 0, 0),
        (2, 1, 1, 0, 1, 2), (2, 2, 0, 0, 1, 1),
        (3, 2, 1, 0, 0, 1), (3, 2, 1, 0, 1, 2),
    }
    if set(y18.vectors) != published_y18:
        raise AssertionError("Yeh-2018 output vectors differ from the published P1--P4 sets")
    if yr.counters["level_counts_json"] != '{"1": 4, "2": 4, "3": 3, "4": 1}':
        raise AssertionError(f"Yeh--Zuo example counts differ: {yr.counters['level_counts_json']}")
    if check(yeh):
        raise AssertionError("the documented Yeh--Zuo counterexample was not detected")
    bai = bai_example(); br = bai_2021(bai)
    if br.counters["level_counts_json"] != '{"1": 8, "2": 16, "3": 8, "4": 1}':
        raise AssertionError(f"Bai example counts differ: {br.counters['level_counts_json']}")
    check(bai, use_oracle=False)
    for key, (net, _d, _expected) in FIXTURES.items():
        if key != "cyclic_small": check(net)
    yeh_complete = yeh_incomplete = 0
    for acyclic in (True, False):
        for seed in range(10):
            net = random_directed_network(5, 6 if acyclic else 8, 1, 2, seed, acyclic)
            if check(net): yeh_complete += 1
            else: yeh_incomplete += 1
    print(f"random audit: literal Yeh--Zuo complete on {yeh_complete}, incomplete on {yeh_incomplete}")
    print("Yeh-2018, Bai-2021, and repeated F-B-2017 passed all literature-example and randomized validations")


if __name__ == "__main__": main()

