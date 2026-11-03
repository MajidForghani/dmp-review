# Principal findings

These values are taken from the frozen summaries in the repository. Times are
medians of three isolated complete-pipeline runs unless otherwise indicated.

## Fixed-demand comparison

- 94 cases, five algorithms, and 1,410 timing observations.
- Every timed execution completed within the common 600-second limit.
- All algorithms returned the same output cardinality and cryptographic set
  digest for every case and repetition.
- Forghani-elahabad and Bonani (2017) had the smallest overall median time
  (0.0110 s), the largest number of case wins (48), and the smallest maximum
  completed time (1.8143 s).
- Lin et al. (1995) won 26 cases and was particularly competitive on the
  SNDlib-derived block, but its mean was affected by a difficult random DAG.
- Wu (2025) was competitive on several acyclic cases but incurred pronounced
  cyclic-flow and memory costs on bidirected networks.
- One separate memory-instrumented Lin run reached the 600-second limit; it is
  retained as a censored memory observation. Its three timing runs completed.

## All-demand comparison

- 37 networks, four recorded methods/roles, and 444 timing observations.
- Bai et al. (2021), Yeh (2018), and repeated Forghani-elahabad--Bonani (2017)
  completed every run and returned identical boundaries at every demand level.
- Bai et al. was fastest on 35 of 37 networks. The two Yeh wins occurred on
  sub-millisecond Abilene-derived cases and are practical ties.
- Bai's median and geometric-mean speedups over repeated fixed-d solution were
  5.17 and 5.91. Bai was faster than repetition on every network.
- Relative to Yeh (2018), Bai's median and geometric-mean speedups were 3.47 and
  3.11.
- On the largest case, containing 291,839 vectors over all levels, Bai required
  3.07 s, repeated fixed-d solution 13.89 s, and Yeh 35.45 s.
- Yeh generated a median 2.66 times as many additions as Bai. On the largest
  case, Yeh formed 2,225,726 additions and removed 1,933,902 duplicates, while
  Bai formed 291,836 additions.

## Yeh--Zuo (2019) correctness diagnostic

- The literal recurrence completed 36 of 37 networks and reached the limit on
  the largest random DAG.
- It returned the complete boundary on 12 of the 36 completed networks and
  omitted valid vectors on 24.
- Across completed networks, it returned 126,264 of the 279,874 vectors in the
  verified boundaries, an aggregate coverage of 45.1%.
- Every returned vector passed independent d-MP verification. The observed
  defect is omission (incompleteness), not the inclusion of invalid vectors.

These findings describe the controlled Python implementations and tested
corpus. They are not universal rankings of the underlying algorithmic ideas.

