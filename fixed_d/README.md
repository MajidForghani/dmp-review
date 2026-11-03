# Fixed-demand d-MP comparison package 1.2.1

> **Public-release note.** This directory now includes the frozen 94-case
> corpus and the complete results used in the manuscript. Validation does not
> require rerunning the timing study. If the experiment is repeated, use a new
> output directory and preserve `results/fixed_d_final/` unchanged.

This is the final fixed-demand experimental package for the major revision of
the d-MP review. It independently implements five complete fixed-demand
enumerators and produces the raw evidence, audits, summaries, tables, and plots
required by the revised manuscript. The separate all-demand experiment is not
part of this package.

## Compared methods

| Package name | Compared component |
|---|---|
| `lin_1995` | Lin, Jane, and Yuan path-flow generation, mapping, deduplication, and minimal-vector filtering. |
| `forghani_bonani_2017` | Algorithms 1–2, including lower bounds, candidate generation, duplicate removal, and cycle-based d-MP verification. |
| `huang_2020` | Binding-LBP generation, including binding groups, binding-flow vectors, mapping, and required minimal comparison. |
| `niu_2020` | Feasible-circulation and disjoint-box enumeration, including every auxiliary maximum-flow and circulation test. |
| `wu_2025` | Frontier decomposition, compressed structure construction, complete DFS materialization, duplicate handling, and cycle filtering. |

Downstream reliability calculation is excluded for every method. Wu's complete
materialization is included because the common output is the explicit set of
all d-MP vectors. See `METHOD_SCOPE.md`.

## Model assumptions

- directed network with one source and one sink;
- integer consecutive states `0,1,...,M_i`;
- ordinary flow conservation at intermediate nodes;
- parallel arcs allowed and self-loops excluded;
- a d-MP is a componentwise-minimal capacity vector supporting demand `d`.

These assumptions make the one-unit decrement test valid. The code should not
be applied unchanged to nonconsecutive component-state spaces.

## What changed in 1.2

- Three timing repetitions and peak-memory measurement are separate. Memory is
  measured once per algorithm-case, so allocation tracing never contaminates
  timing and is not unnecessarily repeated.
- A saved configuration and manifest hash prevent an interrupted run from being
  resumed under different experimental settings.
- The runner records complete phase times, process wall time, timeouts, errors,
  output digests, structural features, and family-specific counters.
- Published examples, held-out random cases, and deterministic SNDlib-derived
  suites can be generated and merged without manual editing.
- Manuscript-ready CSV summaries, TeX tables, performance profiles,
  solved-instance curves, PNG figures, and audit JSON files are generated
  automatically.

## Maintenance correction in 1.2.1

- Fully timed-out cases are now reported separately as `fully_unsolved_cases`;
  they are no longer mislabeled as inconsistent outputs or digests.
- The algorithm implementations are unchanged from 1.2.0. The Wu (2025)
  implementation is also unchanged from versions 1.0 and 1.1.
- The final SNDlib-derived block uses bidirected physical topologies with
  controlled capacities in `[1,2]`. Screening showed that `[3,7]` causes
  pervasive cyclic-flow explosion, whereas the acyclic transformation is too
  small to provide meaningful timing evidence.

Python 3.10 or newer with pandas and matplotlib is required. A normal Anaconda
installation already provides them.

If either package is missing, install the recorded dependencies from the
Spyder IPython console with:

```python
%pip install -r requirements.txt
```

All commands shown below can be entered in Spyder's IPython console by replacing
the leading `python` with `%run`; for example, `%run validate.py` and
`%run prepare_final_random.py`.

## Step 1: validate

From the extracted package directory:

```bash
python validate.py
```

The command compares all five algorithms by exact vector-set equality with an
independent exhaustive oracle on five fixtures and twenty random networks.

## Step 2: create the held-out final base corpus

```bash
python prepare_final_random.py
```

This creates `study/final_base/manifest.json` containing:

- the published/validation examples;
- all random cases with `n` in `{7,8}`, `m=2n`, capacities in `[3,7]`, held-out
  seeds `20,...,24`, DAG and cyclic families, and target demand fractions
  `0.25,0.50,0.75`.

Calibration seeds are excluded. Every generated feasible case is retained; the
corpus is not filtered according to algorithm runtime or output size.

## Step 3: prepare SNDlib-derived cases

The archived topology-only SNDlib-compatible files for `abilene`, `polska`, and
`nobel-us` are included in `sndlib_native/`, together with their provenance
note. To regenerate the screening suite:

```bash
python prepare_sndlib_suite.py --input-dir sndlib_native --mode screen \
  --transformation bidirected --capacity-low 1 --capacity-high 2 \
  --output-dir study/sndlib_screen_bidirected_c1-2
```

The script selects two terminal pairs without using algorithm performance: the
lexicographically first diameter pair and the pair closest to the median
undirected hop distance. Screening capacity seeds are `30,31`.

Run the screen once without memory profiling:

```bash
python run_study.py study/sndlib_screen_bidirected_c1-2/manifest.json \
  --repetitions 1 --timeout 60 --memory none \
  --output results/sndlib_screen/timing_raw.csv
```

After confirming tractability, generate the held-out SNDlib main suite with
capacity seeds `40,41`:

```bash
python prepare_sndlib_suite.py --input-dir sndlib_native --mode main \
  --transformation bidirected --capacity-low 1 --capacity-high 2 \
  --output-dir study/sndlib_main_bidirected_c1-2
```

The source physical links and artificial multistate capacities remain distinct.
The paper must call these **SNDlib-derived** cases and report the transformation,
terminal-pair rule, capacity distribution, and seeds.

## Step 4: combine the final blocks

```bash
python merge_manifests.py study/final_base/manifest.json \
  study/sndlib_main_bidirected_c1-2/manifest.json \
  --output study/fixed_d_complete/manifest.json
```

## Step 5: run the final experiment

```bash
python run_study.py study/fixed_d_complete/manifest.json \
  --repetitions 3 --timeout 600 --memory once --memory-timeout 600 \
  --output results/fixed_d_final/timing_raw.csv
```

The order is rotated between repetitions. Each algorithm-case timing run is a
separate process. The program checkpoints every observation and resumes safely
when the identical command is run again.

## Result files retained in this repository

The final results directory contains:

- `timing_raw.csv`: every timing repetition and every phase;
- `timing_raw_memory.csv`: one independent peak-memory run per completed pair;
- `run_config.json`: package version, algorithms, limits, and manifest hash;
- `environment.json`: Python, OS, processor, CPU-count, and memory information;
- `output_audit.json`: exact-output agreement across algorithms/repetitions;
- `memory_audit.json`: agreement between timing and memory-run outputs;
- `summary/case_algorithm_summary.csv`: median phases, counters, memory, and status;
- `summary/case_summary.csv`: fastest method, output size, and solved status;
- `summary/algorithm_summary.csv`: solved cases, timeouts, wins, time, and memory;
- `summary/phase_summary.csv`: absolute phase costs and shares;
- `summary/structural_summary.csv`: topology/demand/family stratification;
- `summary/performance_profile.csv` and `.png`;
- `summary/solved_instance_curve.csv` and `.png`;
- `summary/algorithm_summary.tex` and `phase_summary.tex`;
- `summary/analysis_checks.json`.

The complete `results/fixed_d_final`, `study/fixed_d_complete`, and two source
study blocks are already included in the public-release tree.

## Timing convention

The common accounting identity is

```text
T_total = T_pre + T_search + T_map + T_dup + T_verify + T_output.
```

`T_pre` includes required MP generation, bounds, ordering, and auxiliary
structures. `T_mp_generation` is also exposed separately for MP-based methods.
`T_output` covers canonical ordering, hashing, and in-memory serialization, but
not reliability calculation or disk/process startup. `wall_total_external` is
an independent check. Integrated operations are assigned to one phase only, so
the six terms do not double count.

Peak memory is the maximum Python allocation traced during a separate complete
execution. It does not include every byte allocated inside the interpreter or
operating system and must be described as peak traced Python allocation.

## Reporting caution

The results compare controlled Python reimplementations, not the original
authors' programs or programming languages. Use solved-case curves, performance
profiles, structural strata, and raw observations. Do not replace timeouts by
the time limit in arithmetic means and do not claim universal superiority from
finite benchmarks.
