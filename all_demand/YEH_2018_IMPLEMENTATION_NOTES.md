# Yeh (2018) implementation notes

Reference: W.-C. Yeh, "Fast Algorithm for Searching d-MPs for All Possible d,"
IEEE Transactions on Reliability, 67(1), 2018, 308--315.
DOI: 10.1109/TR.2017.2771495.

## Implemented scope

`dmpbench.all_algorithms.yeh_2018` implements the complete all-demand task:
given all binary MPs generated from the network, return every ordinary d-MP
for every positive feasible demand from 1 through the maximum flow.

The implementation includes:

- Step 0 binary-MP ordering by logarithmic-prime value;
- Lemma 5's triangular construction for demand 2;
- Lambda-based prevention of infeasible additions (Lemmas 6--11);
- directed-cycle rejection;
- incremental Lambda updates according to Lemma 10;
- logarithmic-prime addition and sorted merging (Lemmas 12--16); and
- exact vector confirmation of duplicates.

## Two transparent implementation decisions

1. Step 1.5 contains an apparent typographical error: it tests `j=|P_d|`, but
   `j` is not the outer loop variable. The executable interpretation uses the
   outer binary-path index `i` and terminates after all members of `P1` have
   been processed.
2. The paper's injectivity argument is exact for prime products, whereas the
   algorithm stores sums of floating-point logarithms. The code uses those
   logarithms for the published ordering and merge operation, but confirms
   equality using the actual integer capacity tuple. This prevents numerical
   collisions without adding candidates or changing the recurrence.

## Validation evidence

- The complete published sets on Fig. 1 are reproduced exactly: level counts
  4, 5, 3, and 1, including `(1,2,0,1,1,0)` at demand 2.
- Yeh-2018 agrees with an independent exhaustive arc-state oracle, Bai-2021,
  and repeated F-B-2017 on all literature fixtures and 20 seeded small random
  networks in `validate.py`.
- In a separate pre-release audit, its output digest agreed with the validated
  Bai-2021 digest on every one of the 37 final study networks. The largest
  audited case contained 291,839 all-level vectors.

These checks test returned sets, not merely output counts.
