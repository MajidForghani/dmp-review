# Reproducible experiments for exact d-MP enumeration

This repository contains the code, frozen benchmark instances, raw observations,
audits, and manuscript-ready summaries used in the computational experiments of
the review:

> **The d-Minimal-Path Problem in Multistate Flow Networks: A Critical Review of
> Models, Exact Algorithms, and Computational Evidence**

The implementations are independent Python reconstructions of the published
algorithms. They are not the original authors' programs and should not be used
to infer language-independent or implementation-independent rankings.

## Experiments

| Study | Compared methods | Corpus | Common limit |
|---|---|---:|---:|
| Fixed demand | Lin et al. (1995); Forghani-elahabad and Bonani (2017); Huang et al. (2020); Niu et al. (2020); Wu (2025) | 94 fixed-demand cases | 600 s per algorithm-case |
| All demands | Yeh (2018); Bai et al. (2021); repeated Forghani-elahabad and Bonani (2017) | 37 networks | 1,200 s per complete all-demand execution |
| Correctness diagnostic | Literal Yeh and Zuo (2019) recurrence | Same 37 networks | 1,200 s per execution |

The all-demand performance ranking excludes the literal Yeh--Zuo recurrence
whenever its output is incomplete.

## Repository layout

```text
fixed_d/
  dmpbench/                 algorithm implementations and common model
  study/                    frozen 94-case corpus and source blocks
  results/fixed_d_final/    raw timing/memory data, audits, tables, and plots
all_demand/
  dmpbench/                 all-demand implementations and fixed-d baseline
  study/all_demand_final/   frozen 37-network corpus
  results/all_demand_final/ raw timing/memory data, audits, tables, and plots
RESULTS.md                  concise numerical findings
PROVENANCE.md               source archives and public-release normalization
CITATION.cff                citation metadata
```

## Quick validation

Python 3.10 or newer is required. From the repository root:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python verify_release.py
python fixed_d/validate.py
python all_demand/validate.py
```

On Windows, the virtual environment can be activated with
`.venv\Scripts\activate`; on Linux or macOS, use `source .venv/bin/activate`.

The fixed-demand validation compares all five methods with an independent
exhaustive oracle on the published fixtures and twenty small random networks.
The all-demand validation checks Yeh (2018), Bai et al. (2021), and repeated
fixed-d solution against exact enumeration and deliberately confirms the
documented omission in the literal Yeh--Zuo recurrence. That diagnostic message
is expected and is not a validation failure.

## Frozen results used in the manuscript

No execution is needed to inspect or reproduce the reported tables. The exact
raw observations used in the manuscript are already included:

- `fixed_d/results/fixed_d_final/timing_raw.csv`
- `fixed_d/results/fixed_d_final/timing_raw_memory.csv`
- `all_demand/results/all_demand_final/timing_raw.csv`
- `all_demand/results/all_demand_final/timing_raw_memory.csv`

Each results folder also contains the saved configuration, environment record,
output audits, per-case summaries, phase summaries, performance profiles, and
manuscript-ready TeX tables.

## Re-running the complete experiments

The full studies may take hours. Use a new output directory so that the frozen
observations are never overwritten.

Fixed demand:

```bash
cd fixed_d
python run_study.py study/fixed_d_complete/manifest.json \
  --repetitions 3 --timeout 600 --memory once --memory-timeout 600 \
  --output results/reproduction_fixed_d/timing_raw.csv
```

All demands:

```bash
cd all_demand
python run_study.py study/all_demand_final/manifest.json \
  --repetitions 3 --timeout 1200 --memory once --memory-timeout 1200 \
  --output results/reproduction_all_demand/timing_raw.csv
```

Runtime values are hardware- and software-dependent. Correctness should be
checked by output cardinalities and cryptographic set digests, not by expecting
identical wall-clock times.

## Timing and memory convention

The measured pipeline is

```text
T_total = T_pre + T_search + T_map + T_dup + T_verify + T_output.
```

Required preprocessing, candidate generation, mapping, duplicate handling,
minimality verification, and complete in-memory output materialization are
included. Downstream reliability calculation is excluded. Peak memory denotes
peak traced Python allocation from a separate complete execution and is not an
operating-system resident-set measurement.

## Benchmark provenance

The random cases use fixed held-out seeds. The SNDlib-derived cases preserve the
Abilene, Polska, and Nobel-US physical topologies, replace each physical link by
two directed arcs, and assign controlled integer capacities using recorded
seeds. The archived topology-only inputs and their provenance note are included
under each study's `sndlib_native/` directory.

## Citation and licensing

Please cite the associated review and this repository release. Citation metadata
is supplied in `CITATION.cff`.

No reuse license has been selected in this archive. Before public release, the
authors may add their preferred license; a common arrangement is an open-source
license for code and a data/documentation license for archived results.

