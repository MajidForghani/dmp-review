# Frozen all-demand experimental design

## Research questions

1. When is a dedicated all-demand method faster or more memory-efficient than
   repeated independent fixed-d solution?
2. How do alternative upward constructions and repeated solution respond to topology,
   binary-path multiplicity, maximum flow, and boundary size?
3. Does a subtraction-based recurrence preserve completeness, and what failure
   mode occurs when a d-MP is not contained in any `(d+1)`-MP?

## Comparator decision

Repeated F-B-2017 is the sole fixed-d baseline because it was the stable,
general-purpose performer in the preceding common-platform study. Wu-2025 is
not added: its strong DAG results and severe cyclic/bidirected deterioration are
already documented by the fixed-d experiment, and repeating it here would add
substantial cost without changing the all-demand research question.

## Limits and repetitions

- Three timing repetitions in separate processes.
- Rotated algorithm order.
- One independent peak traced-Python-memory run per algorithm-network pair
  that completes at least one timing run.
- 1,200 seconds for each complete all-demand method-network execution.
- Exact order-independent output digests retained for every successful run.
- Timeouts are censored outcomes, not values inserted into arithmetic means.

## Primary and diagnostic analyses

Primary speed, win, solved-case, and performance-profile results compare
repeated F-B-2017, Yeh-2018, and Bai-2021 because all three passed the validation suite.
Literal Yeh--Zuo-2019 runtime, output size, level counts, and missing-output
behavior are retained separately as a correctness and failure-mode diagnostic.
