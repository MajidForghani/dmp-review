# Method scope and reviewer-comment mapping

## Do the five papers enumerate the same object?

Yes, under the common directed, integer-capacity, consecutive-state model used
by this package. Each selected method can be restricted to the stage that
enumerates all componentwise lower boundary vectors for one fixed demand `d`.

The restrictions must be disclosed:

1. **Lin et al. (1995):** the compared portion enumerates feasible path-flow
   assignments of value `d`, maps them to arc vectors, and retains the minimal
   vectors. Its reliability-evaluation stage is not timed.
2. **Forghani-elahabad and Bonani (2017):** Algorithms 1–2 constitute the d-MP
   enumerator. Lower-bound preprocessing, hashing, and verification are included;
   reliability evaluation and application-specific extensions are excluded.
3. **Huang et al. (2020):** the paper calls the outputs lower boundary points.
   In this model these are d-MPs. The binding-group enumeration is included; the
   later reliability calculation is excluded. The package preserves the paper's
   special residual-group case and uses a global minimal comparison there.
4. **Niu et al. (2020):** its feasible-circulation/disjoint-box method directly
   enumerates all multistate minimal paths for a fixed demand. Boundary boxes,
   circulation tests, partitioning, and verification are included.
5. **Wu (2025):** the paper additionally emphasizes compressed storage. For a
   fair enumeration comparison, both construction of the compressed structure
   and complete DFS materialization of every d-MP are included. Reporting only
   structure-construction time would answer a different question.

Thus the final table should label the target **fixed-d complete d-MP
enumeration**, and a footnote should identify the excluded downstream reliability
calculations and Wu's included materialization stage.

## Reviewer coverage

| Comment | Contribution of this fixed-d experiment | What still remains |
|---|---|---|
| Reviewer 1, Comment 1 | Directly supplies a common implementation platform, common instances, full phase timing, memory, candidates, and correctness checks for Tables 3–4. | Insert final data, hardware/software details, statistical summaries, and revise qualitative judgments accordingly. |
| Reviewer 1, Comment 2 | None beyond identifying strong single-d baselines. | Address later with the all-demand experiment and a reasoned comparison of upward, subtraction, and repeated fixed-d solving. |
| Reviewer 2, Comment 2 | The package improves reproducibility of experiments only. | The literature-review databases, dates, queries, screening criteria, flow diagram, and included-study counts remain separate work. |
| Reviewer 2, Comment 4 | Candidate growth and topology/demand effects can support interpretation of descriptive patterns. | Figures 1–3 still require substantive interpretation tied to methodological developments and gaps. |
| Reviewer 2, Comment 5 | Directly strengthens comparison of correctness, limitations, candidate counts, memory, and observed performance. | Add theoretical complexity/correctness qualifications from the papers; do not replace theory with benchmarks. |
| Reviewer 2, Comment 7 | Directly operationalizes the six-part runtime decomposition and adds quantitative evidence. | Insert final plots/tables and discuss where time and memory are spent. |
| Reviewer 2, Comment 8 | Can empirically support fixed-d recommendations and clearly separate measured findings from hypotheses. | Revise Tables 7–8 after both fixed-d and all-demand studies; label untested recommendations explicitly. |
| Reviewer 3, Comment 1 | Supports the title phrase “Computational Evidence” if the final manuscript includes the controlled results and correctness validation. | Reassess the title after both experiments and state the distinction from earlier surveys. |
| Reviewer 3, Comment 4 | Provides empirical fixed-d selection evidence. | The conditions favoring all-demand directions belong to the later experiment and theoretical discussion. |

## Recommended manuscript language

“We independently reimplemented the fixed-demand enumeration components of five
representative methods under one Python environment. Downstream reliability
evaluation was excluded. For Wu's compressed representation, complete output
materialization was included so that every method was timed against the same
task: returning the full set of d-MP vectors.”

Use “independently reimplemented” rather than implying that the original authors'
code was executed. Treat observed rankings as implementation- and benchmark-
dependent evidence, not universal dominance.
