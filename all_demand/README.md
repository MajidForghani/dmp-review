# All-demand d-MP comparison package 1.1.0 FINAL

> **Public-release note.** This directory includes the frozen 37-network corpus
> and the complete results used in the manuscript. Validation does not require
> rerunning the timing study. If the experiment is repeated, use a new output
> directory and preserve `results/all_demand_final/` unchanged.

This package supports the all-demand experiment for the major revision of the
d-MP review. It independently reconstructs three all-demand methods and compares
them with repeated independent execution of the robust fixed-demand baseline.

## Methods and roles

| Package name | Role |
|---|---|
| `repeated_fb_2017` | Primary exact baseline: independently run Forghani-elahabad and Bonani (2017) for every `d=1,...,dmax`. |
| `yeh_2018` | Primary exact all-demand method: Yeh (2018), including Lambda prevention, cycle rejection, and logarithmic-prime merge ordering with exact vector confirmation. |
| `bai_2021` | Primary exact all-demand method: Bai et al. (2021), including Lambda and rho duplicate-prevention rules. |
| `yeh_zuo_2019` | Literal diagnostic reconstruction of Yeh and Zuo (2019). It is not included in primary performance rankings because its containment lemma fails on its own example; see `CORRECTNESS_AUDIT.md`. |

Only one repeated fixed-d baseline is used. The preceding fixed-d study showed
that Forghani-elahabad and Bonani (2017) was strong and robust across random and
SNDlib-derived blocks. Wu (2025) was sometimes faster on acyclic networks but
showed severe topology-dependent deterioration on cyclic/bidirected cases.
Adding it here would duplicate the fixed-d question and greatly increase the
study cost without providing a stable general-purpose comparator.

## Common task and timing rule

The task is complete explicit enumeration of every ordinary d-MP for every
positive feasible demand. Downstream reliability calculation is excluded.

The accounting identity is

`T_total = T_pre + T_search + T_map + T_dup + T_verify + T_output`.

Every algorithm-network execution receives one 1,200-second limit for the
complete all-demand task. The repeated fixed-d method does not receive 1,200
seconds separately for each demand. Three isolated timing repetitions and one
separate peak-memory run are used. Runs are checkpointed and resumable.

Yeh and Zuo (2019) assume that `P1` and `P_dmax` are already available. The
end-to-end time in this package includes binary-MP generation and construction
of `P_dmax` with the selected fixed-d solver. The latter is also exposed as
`T_seed_dmax`.

## Corpus

`prepare_all_demand_corpus.py` creates 37 distinct networks by collapsing the
demand-specific copies in the fixed-d corpus:

- 5 published or validation examples;
- 20 held-out random networks (`n` in `{7,8}`, `m=2n`, capacities 3--7,
  seeds 20--24, DAG and cyclic families); and
- 12 SNDlib-derived networks (Abilene, Polska, Nobel-US; two deterministic
  terminal pairs, seeds 40--41, bidirected links, capacities 1--2).

## Spyder instructions

Extract the package, open Spyder, and set its working directory to the folder
containing this README. Then enter these commands in the IPython console.

### 1. Install dependencies if necessary

```python
%pip install -r requirements.txt
```

Restart the IPython kernel after installation.

### 2. Validate the implementations

```python
%run validate.py
```

Expected conclusion: Bai-2021 and repeated F-B-2017 pass the literature and
random oracle checks. Yeh-2018 must reproduce its published 4/5/3/1 counts and
agree with both exact methods. The script must also detect the documented literal
Yeh--Zuo omission; that message is an expected audit result, not a package
failure.

### 3. Create the 37-network corpus

```python
%run prepare_all_demand_corpus.py
```

### 4. Run the final experiment

```python
%run run_study.py study/all_demand_final/manifest.json --repetitions 3 --timeout 1200 --memory once --memory-timeout 1200 --output results/all_demand_final/timing_raw.csv
```

The command can take many hours. If Spyder or Windows is interrupted, enter
the identical command again. Completed rows are not rerun. Do not change the
manifest, algorithms, repetition count, or limits when resuming the same
results folder.

The output disagreement audit is deliberately retained because the literal
Yeh--Zuo method can omit valid vectors. To make any disagreement abort the run,
add `--strict-output`; this is not recommended for the present diagnostic study.

## Files retained in this repository

The public release includes both complete folders:

1. `results/all_demand_final`
2. `study/all_demand_final`

The results folder includes raw timing and memory observations, configuration,
environment details, exact-output audits, summaries, TeX tables, and plots.
The raw observations, audits, and complete summaries are retained rather than
only screenshots or the aggregate `algorithm_summary.csv`.

## Reporting limits

These are controlled Python reimplementations, not author-supplied programs.
The primary performance comparison includes Yeh (2018), Bai et al. (2021), and
repeated Forghani-elahabad and Bonani (2017). Yeh and Zuo (2019) is reported as
a correctness/failure-mode diagnostic unless a mathematically valid correction
is developed and clearly labelled as a new variant.

## Faithful implementation notes for Yeh (2018)

The implementation follows Steps 0--2 and Lemmas 5--16. The apparent `j` in
Step 1.5 is interpreted as the outer index `i`; otherwise the loop has no
coherent stopping condition. The paper's logarithmic-prime value is retained
for ordering and merging, while actual vector tuples confirm equality. This
prevents floating-point roundoff from silently merging different vectors or
retaining duplicate vectors. These two transparent engineering decisions are
recorded in the manuscript-facing documentation.
