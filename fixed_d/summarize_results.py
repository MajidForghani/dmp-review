"""Create manuscript-ready tables, profiles, curves, and audit summaries."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path, PureWindowsPath

import pandas as pd

PHASES = ["pre", "search", "map", "dup", "verify", "output"]
LABELS = {
    "lin_1995": "Lin et al. (1995)",
    "forghani_bonani_2017": "Forghani-elahabad and Bonani (2017)",
    "huang_2020": "Huang et al. (2020)",
    "niu_2020": "Niu et al. (2020)",
    "wu_2025": "Wu (2025)",
}


def basename(value: str) -> str:
    return PureWindowsPath(value).name if "\\" in str(value) else Path(value).name


def latex_escape(value: object) -> str:
    return str(value).replace("_", r"\_").replace("%", r"\%")


def write_latex_table(df: pd.DataFrame, path: Path, columns: list[str], headers: list[str]) -> None:
    align = "l" + "r" * (len(columns) - 1)
    lines = [r"\begin{tabular}{" + align + "}", r"\toprule",
             " & ".join(headers) + " \\\\", r"\midrule"]
    for _, row in df.iterrows():
        vals = []
        for col in columns:
            x = row.get(col, "")
            if pd.isna(x): vals.append("--")
            elif isinstance(x, float): vals.append(f"{x:.4g}")
            else: vals.append(latex_escape(x))
        lines.append(" & ".join(vals) + " \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("timing")
    p.add_argument("--memory")
    p.add_argument("--manifest", required=True)
    p.add_argument("--output-dir", default="results/summary")
    a = p.parse_args(); out = Path(a.output_dir); out.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(a.timing); raw["case_id"] = raw["instance_path"].map(basename)
    manifest = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    records = pd.DataFrame(manifest["instances"])
    records["case_id"] = records["path"].map(basename)
    records = records.drop(columns=["path"], errors="ignore").drop_duplicates("case_id")
    algorithms = list(dict.fromkeys(raw["algorithm"].tolist())); cases = sorted(raw["case_id"].unique())
    numeric = [c for c in raw.columns if c.startswith("T_") or c in {
        "wall_total_external", "binary_paths", "raw_path_flows", "raw_candidates",
        "distinct_candidates", "distinct_group_candidates", "duplicate_candidates_removed",
        "minimality_rejections", "cycle_rejections", "binding_groups", "binding_flow_vectors",
        "initial_boxes", "boxes_examined", "boxes_pruned_upper", "circulation_tests", "d_flows",
        "max_flow_calls", "d_flow_candidates", "dd_nodes", "dd_arcs", "dd_peak_width",
        "output_count", "output_bytes", "T_mp_generation", "mean_path_length",
        "max_path_length", "max_arc_path_overlap", "mean_arc_path_overlap",
        "path_arc_incidences", "maximum_flow", "demand_fraction_actual", "n", "m", "demand"}]
    for c in numeric:
        if c in raw: raw[c] = pd.to_numeric(raw[c], errors="coerce")
    rows = []
    for case_id in cases:
        for alg in algorithms:
            g = raw[(raw.case_id == case_id) & (raw.algorithm == alg)]
            good = g[g.status == "ok"]
            row = {"case_id": case_id, "algorithm": alg, "algorithm_label": LABELS.get(alg, alg),
                   "completed_repetitions": len(good), "timeout_repetitions": int((g.status == "timeout").sum()),
                   "error_repetitions": int((g.status == "error").sum()),
                   "all_repetitions_completed": int(len(good) == len(g) and len(g) > 0)}
            for c in numeric:
                if c in good and good[c].notna().any(): row[c] = good[c].median()
            if len(good) > 1 and good["T_total"].mean() > 0:
                row["T_total_cv"] = good["T_total"].std(ddof=1) / good["T_total"].mean()
            if len(good):
                row["output_digest"] = good.output_digest.iloc[0]
                row["digest_consistent_across_repetitions"] = int(good.output_digest.nunique() == 1)
            rows.append(row)
    ca = pd.DataFrame(rows).merge(records, on="case_id", how="left", suffixes=("", "_manifest"))
    if a.memory and Path(a.memory).exists():
        mem = pd.read_csv(a.memory); mem["case_id"] = mem.instance_path.map(basename)
        mem["peak_memory_bytes"] = pd.to_numeric(mem.get("peak_memory_bytes"), errors="coerce")
        mem = mem[mem.status == "ok"][["case_id", "algorithm", "peak_memory_bytes", "memory_wall_seconds"]]
        ca = ca.merge(mem, on=["case_id", "algorithm"], how="left")
    ca.to_csv(out / "case_algorithm_summary.csv", index=False)

    successful = ca[ca.completed_repetitions > 0].copy()
    successful["rank"] = successful.groupby("case_id")["T_total"].rank(method="min")
    successful["winner"] = (successful["rank"] == 1).astype(int)
    alg_rows = []
    for alg in algorithms:
        g = ca[ca.algorithm == alg]; s = successful[successful.algorithm == alg]
        alg_rows.append({"algorithm": alg, "algorithm_label": LABELS.get(alg, alg),
                         "cases": len(g), "cases_solved": int((g.completed_repetitions > 0).sum()),
                         "cases_all_repetitions": int(g.all_repetitions_completed.sum()),
                         "cases_with_timeout": int((g.timeout_repetitions > 0).sum()),
                         "cases_failed_all": int((g.completed_repetitions == 0).sum()),
                         "wins": int(s.winner.sum()), "median_time_seconds": s.T_total.median(),
                         "mean_time_seconds_completed": s.T_total.mean(),
                         "max_time_seconds_completed": s.T_total.max(),
                         "median_peak_memory_bytes": s.get("peak_memory_bytes", pd.Series(dtype=float)).median(),
                         "max_peak_memory_bytes": s.get("peak_memory_bytes", pd.Series(dtype=float)).max(),
                         "median_output_count": s.output_count.median()})
    alg = pd.DataFrame(alg_rows).sort_values(["cases_solved", "median_time_seconds"], ascending=[False, True])
    alg.to_csv(out / "algorithm_summary.csv", index=False)

    phase_rows = []
    for alg_name, g in successful.groupby("algorithm"):
        row = {"algorithm": alg_name, "algorithm_label": LABELS.get(alg_name, alg_name)}
        for phase in PHASES:
            col = f"T_{phase}"; row[f"median_{col}"] = g[col].median()
            row[f"median_share_{phase}"] = (g[col] / g.T_total).median()
        phase_rows.append(row)
    phase = pd.DataFrame(phase_rows); phase.to_csv(out / "phase_summary.csv", index=False)

    case_rows = []
    for case_id, g in ca.groupby("case_id"):
        s = g[g.completed_repetitions > 0]
        row = {"case_id": case_id, "algorithms_solved": len(s),
               "algorithms_timed_out": int((g.timeout_repetitions > 0).sum()),
               "fastest_algorithm": (s.loc[s.T_total.idxmin(), "algorithm"] if len(s) else ""),
               "fastest_time_seconds": (s.T_total.min() if len(s) else math.nan),
               "slowest_completed_time_seconds": (s.T_total.max() if len(s) else math.nan),
               "output_count": (s.output_count.iloc[0] if len(s) else math.nan),
               "output_count_consistent": int(s.output_count.nunique() <= 1) if len(s) else pd.NA,
               "digest_consistent": int(s.output_digest.nunique() <= 1) if len(s) else pd.NA}
        for c in ("family", "seed", "demand", "demand_label", "target_fraction", "actual_fraction",
                  "maximum_flow", "benchmark_block", "topology", "transformation", "terminal_pair_label"):
            if c in g and g[c].notna().any(): row[c] = g[c].dropna().iloc[0]
        case_rows.append(row)
    cases_df = pd.DataFrame(case_rows); cases_df.to_csv(out / "case_summary.csv", index=False)

    tau_values = [1, 1.25, 1.5, 2, 3, 5, 10, 20, 50, 100]
    profiles = []
    for case_id, g in ca.groupby("case_id"):
        solved = g[g.completed_repetitions > 0]
        best = solved.T_total.min() if len(solved) else math.nan
        for _, row in g.iterrows():
            ratio = row.T_total / best if row.completed_repetitions > 0 and best > 0 else math.inf
            for tau in tau_values:
                profiles.append({"case_id": case_id, "algorithm": row.algorithm, "tau": tau,
                                 "solved_within_tau": int(ratio <= tau)})
    prof = pd.DataFrame(profiles).groupby(["algorithm", "tau"], as_index=False).solved_within_tau.mean()
    prof = prof.rename(columns={"solved_within_tau": "fraction_of_cases"})
    prof.to_csv(out / "performance_profile.csv", index=False)

    time_values = [0.001, 0.01, 0.1, 1, 10, 60, 600]
    curves = []
    for alg_name in algorithms:
        g = ca[ca.algorithm == alg_name]
        for limit in time_values:
            count = int(((g.completed_repetitions > 0) & (g.T_total <= limit)).sum())
            curves.append({"algorithm": alg_name, "time_seconds": limit,
                           "cases_solved": count, "fraction_solved": count / len(g) if len(g) else 0})
    curve = pd.DataFrame(curves); curve.to_csv(out / "solved_instance_curve.csv", index=False)

    group_cols = [c for c in ("family", "demand_label", "benchmark_block", "algorithm") if c in ca]
    if len(group_cols) > 1:
        fam = successful.groupby(group_cols, dropna=False).agg(
            cases_solved=("case_id", "size"), median_time_seconds=("T_total", "median"),
            median_output_count=("output_count", "median")).reset_index()
        fam.to_csv(out / "structural_summary.csv", index=False)

    write_latex_table(alg, out / "algorithm_summary.tex",
                      ["algorithm_label", "cases_solved", "cases_with_timeout", "wins",
                       "median_time_seconds", "max_time_seconds_completed", "median_peak_memory_bytes"],
                      ["Algorithm", "Solved", "Timeout", "Wins", "Median time (s)",
                       "Max completed (s)", "Median peak memory (bytes)"])
    phase_tex = phase.copy()
    write_latex_table(phase_tex, out / "phase_summary.tex",
                      ["algorithm_label"] + [f"median_T_{p}" for p in PHASES],
                      ["Algorithm"] + [f"$T_{{\\rm {p}}}$" for p in PHASES])

    checks = {"timing_rows": len(raw), "cases": len(cases), "algorithms": algorithms,
              "expected_case_algorithm_pairs": len(cases) * len(algorithms),
              "case_algorithm_rows": len(ca),
              "inconsistent_repetition_digests": int((ca.get("digest_consistent_across_repetitions", 1) == 0).sum()),
              "fully_unsolved_cases": int((cases_df.algorithms_solved == 0).sum()),
              "inconsistent_case_outputs": int(((cases_df.algorithms_solved > 0) &
                                                  (cases_df.output_count_consistent == 0)).sum()),
              "inconsistent_case_digests": int(((cases_df.algorithms_solved > 0) &
                                                  (cases_df.digest_consistent == 0)).sum())}
    (out / "analysis_checks.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")

    try:
        import matplotlib.pyplot as plt
        for data, x, y, name, xlabel, ylabel, logx in [
            (prof, "tau", "fraction_of_cases", "performance_profile.png", "Performance ratio", "Fraction of cases", True),
            (curve, "time_seconds", "fraction_solved", "solved_instance_curve.png", "Time limit (s)", "Fraction solved", True)]:
            fig, ax = plt.subplots(figsize=(6.4, 4.2))
            for alg_name, g in data.groupby("algorithm"):
                ax.plot(g[x], g[y], marker="o", linewidth=1.6, label=LABELS.get(alg_name, alg_name))
            if logx: ax.set_xscale("log")
            ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_ylim(0, 1.03); ax.grid(True, alpha=.25)
            ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(out / name, dpi=300); plt.close(fig)
    except ImportError:
        (out / "PLOTS_NOT_GENERATED.txt").write_text(
            "Install matplotlib and rerun summarize_results.py to create the two PNG figures.\n", encoding="utf-8")

    findings = ["# Automatically generated fixed-demand evidence summary", "",
                f"Cases: {len(cases)}. Algorithms: {len(algorithms)}. Raw timing rows: {len(raw)}.", "",
                "The CSV and TeX files in this directory are generated from median phase times across successful repetitions.",
                "Timeouts are retained in solved-instance curves and performance profiles; they are not replaced by the timeout value in averages.",
                "Interpretive manuscript claims should be written only after checking structural_summary.csv and the raw observations."]
    (out / "README_SUMMARY.md").write_text("\n".join(findings) + "\n", encoding="utf-8")
    print(f"summary written to {out}")


if __name__ == "__main__": main()
