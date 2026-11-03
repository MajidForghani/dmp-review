# Mapping from reviewer/manuscript requirements to package outputs

| Requirement | Package evidence |
|---|---|
| Same explicit d-MP output | `output_digest`, `output_count`, `output_audit.json` |
| Complete timing identity | six `T_*` columns, `T_total`, `wall_total_external`, `phase_summary.csv` |
| MP acquisition visible | `T_mp_generation`, `binary_paths`, path-incidence and overlap counters |
| Raw/distinct candidates | `raw_path_flows`, `raw_candidates`, `distinct_candidates`, duplicate/minimality rejections |
| Binding behavior | `binding_groups`, `binding_flow_vectors`, `distinct_group_candidates` |
| Circulation/partition work | `initial_boxes`, `boxes_examined`, pruning, `max_flow_calls`, `circulation_tests` |
| Decomposition/storage work | `dd_nodes`, `dd_arcs`, `dd_peak_width`, `d_flow_candidates`, explicit output count |
| Peak memory | one independent row in `timing_raw_memory.csv` |
| Timeouts/errors | explicit status, process elapsed time, timeout limit, solved-instance curve |
| Structural variation | DAG/cyclic, published, and SNDlib-derived blocks; demand fraction, capacity, density, output size |
| Reproducibility | raw instances, manifests, manifest hash, run configuration, seeds, environment, package version |
| Reviewer 1.1 | all preceding items plus profiles, curves, raw observations, TeX summaries |
| Reviewer 2.5 and 2.7 | complexity-driving counters, phase costs, correctness and limitations by family |
| Reviewer 2.8 | evidence for revising fixed-demand recommendations; all-demand claims remain separate |
| Reviewer 3.1 | controlled computational evidence supporting the title if the final results are included |

Reviewer 1.2 and Reviewer 3.4 concern all-demand enumeration and are not claimed
as addressed by this fixed-demand package.
