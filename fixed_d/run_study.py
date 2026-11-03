"""Checkpointed fixed-d study runner with isolated timing and memory passes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from dmpbench.algorithms import ALGORITHMS
from dmpbench.runner import append_csv, environment_record

PACKAGE_VERSION = "1.2.1"


def prior_keys(path: Path) -> set[tuple[str, str, str]]:
    if not path.exists(): return set()
    with path.open(newline="", encoding="utf-8") as f:
        return {(r.get("instance_path", ""), r["algorithm"], r["run_id"])
                for r in csv.DictReader(f)}


def read_rows(path: Path) -> list[dict]:
    if not path.exists(): return []
    with path.open(newline="", encoding="utf-8") as f: return list(csv.DictReader(f))


def audit_outputs(path: Path, expected_algorithms: list[str], repetitions: int) -> dict:
    groups: dict[tuple[str, str], list[dict]] = {}
    for row in read_rows(path):
        groups.setdefault((row.get("instance_path", ""), row["run_id"]), []).append(row)
    disagreements, incomplete = [], []
    for (instance, run_id), rows in groups.items():
        present = {r["algorithm"] for r in rows}
        if present != set(expected_algorithms):
            incomplete.append({"instance_path": instance, "run_id": run_id,
                               "missing": sorted(set(expected_algorithms) - present)})
        good = [r for r in rows if r.get("status") == "ok"]
        digests = {r.get("output_digest") for r in good}
        if len(digests) > 1:
            disagreements.append({"instance_path": instance, "run_id": run_id,
                                  "algorithms": {r["algorithm"]: r.get("output_digest") for r in good}})
    return {"groups_checked": len(groups), "expected_repetitions": repetitions,
            "incomplete_groups": incomplete, "disagreements": disagreements}


def memory_audit(timing: Path, memory: Path) -> dict:
    references: dict[tuple[str, str], set[str]] = {}
    for row in read_rows(timing):
        if row.get("status") == "ok":
            references.setdefault((row["instance_path"], row["algorithm"]), set()).add(row["output_digest"])
    rows = read_rows(memory); disagreements = []
    for row in rows:
        if row.get("status") != "ok": continue
        key = (row["instance_path"], row["algorithm"])
        if row.get("output_digest") not in references.get(key, set()):
            disagreements.append({"instance_path": key[0], "algorithm": key[1],
                                  "memory_digest": row.get("output_digest"),
                                  "timing_digests": sorted(references.get(key, set()))})
    observed = {(r.get("instance_path", ""), r.get("algorithm", "")) for r in rows}
    missing = sorted([{"instance_path": key[0], "algorithm": key[1]}
                      for key in set(references) - observed],
                     key=lambda x: (x["instance_path"], x["algorithm"]))
    unsuccessful = [{"instance_path": r.get("instance_path", ""),
                     "algorithm": r.get("algorithm", ""),
                     "status": r.get("status", "")}
                    for r in rows if r.get("status") != "ok"]
    return {"memory_rows": len(rows), "expected_memory_pairs": len(references),
            "missing_pairs": missing, "unsuccessful_rows": unsuccessful,
            "disagreements": disagreements}


def main() -> None:
    p = argparse.ArgumentParser(description="Run a reproducible fixed-demand d-MP study")
    p.add_argument("manifest")
    p.add_argument("--algorithms", nargs="+", choices=sorted(ALGORITHMS), default=list(ALGORITHMS))
    p.add_argument("--repetitions", type=int, default=3)
    p.add_argument("--timeout", type=float, default=600, help="seconds for each timing execution")
    p.add_argument("--memory", choices=("once", "none"), default="once")
    p.add_argument("--memory-timeout", type=float, default=None)
    p.add_argument("--max-paths", type=int, default=1_000_000)
    p.add_argument("--no-memory-profile", action="store_true", help="deprecated alias for --memory none")
    p.add_argument("--output", default="results/timing_raw.csv")
    p.add_argument("--memory-output", default=None)
    p.add_argument("--no-summary", action="store_true")
    a = p.parse_args()
    if a.no_memory_profile: a.memory = "none"
    if a.memory_timeout is None: a.memory_timeout = a.timeout
    manifest_path = Path(a.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = Path(a.output); output.parent.mkdir(parents=True, exist_ok=True)
    memory_output = Path(a.memory_output) if a.memory_output else output.with_name(output.stem + "_memory.csv")
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    config = {"package_version": PACKAGE_VERSION, "manifest": str(manifest_path),
              "manifest_sha256": manifest_sha, "algorithms": a.algorithms,
              "repetitions": a.repetitions, "timeout_seconds": a.timeout,
              "memory_mode": a.memory, "memory_timeout_seconds": a.memory_timeout,
              "max_paths": a.max_paths, "timing_output": str(output.resolve()),
              "memory_output": str(memory_output.resolve()),
              "started_utc": datetime.now(timezone.utc).isoformat()}
    config_path = output.with_name("run_config.json")
    if config_path.exists():
        old = json.loads(config_path.read_text(encoding="utf-8"))
        for key in ("package_version", "manifest_sha256", "algorithms", "repetitions",
                    "timeout_seconds", "memory_mode", "memory_timeout_seconds", "max_paths"):
            if old.get(key) != config.get(key):
                raise SystemExit(f"refusing to resume with changed {key}: {old.get(key)!r} != {config.get(key)!r}")
        config["started_utc"] = old.get("started_utc", config["started_utc"])
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    root = Path(__file__).resolve().parent; done = prior_keys(output)
    for item in manifest["instances"]:
        ipath = str(Path(item["path"]).resolve())
        for rep in range(a.repetitions):
            names = a.algorithms[rep % len(a.algorithms):] + a.algorithms[:rep % len(a.algorithms)]
            for name in names:
                key = (ipath, name, str(rep))
                if key in done: continue
                cmd = [sys.executable, str(root / "run_one.py"), ipath, name, str(rep),
                       "--max-paths", str(a.max_paths), "--no-memory-profile"]
                row = {"instance_path": ipath, "algorithm": name, "run_id": rep}
                started = datetime.now(timezone.utc).isoformat(); clock = perf_counter()
                try:
                    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=a.timeout, check=False)
                    if proc.returncode == 0:
                        row.update(json.loads(proc.stdout.strip().splitlines()[-1])); row["status"] = "ok"
                    else:
                        row.update(status="error", error=proc.stderr[-2000:], return_code=proc.returncode)
                except subprocess.TimeoutExpired:
                    row.update(status="timeout", timeout_seconds=a.timeout)
                row.update(process_wall_seconds=perf_counter() - clock, started_utc=started,
                           finished_utc=datetime.now(timezone.utc).isoformat())
                append_csv(output, [row]); done.add(key)
                print(f"{row['status']:7s} {Path(ipath).name} {name} rep={rep}", flush=True)

    if a.memory == "once":
        mem_done = prior_keys(memory_output)
        timing_ok = {(r["instance_path"], r["algorithm"]) for r in read_rows(output) if r.get("status") == "ok"}
        for item in manifest["instances"]:
            ipath = str(Path(item["path"]).resolve())
            for name in a.algorithms:
                key = (ipath, name, "memory")
                if key in mem_done: continue
                row = {"instance_path": ipath, "algorithm": name, "run_id": "memory"}
                if (ipath, name) not in timing_ok:
                    row["status"] = "skipped_no_completed_timing"
                else:
                    cmd = [sys.executable, str(root / "run_memory.py"), ipath, name,
                           "--max-paths", str(a.max_paths)]
                    clock = perf_counter()
                    try:
                        proc = subprocess.run(cmd, capture_output=True, text=True,
                                              timeout=a.memory_timeout, check=False)
                        if proc.returncode == 0:
                            row.update(json.loads(proc.stdout.strip().splitlines()[-1])); row["status"] = "ok"
                        else:
                            row.update(status="error", error=proc.stderr[-2000:], return_code=proc.returncode)
                    except subprocess.TimeoutExpired:
                        row.update(status="timeout", timeout_seconds=a.memory_timeout)
                    row["process_wall_seconds"] = perf_counter() - clock
                append_csv(memory_output, [row]); mem_done.add(key)
                print(f"memory {row['status']:26s} {Path(ipath).name} {name}", flush=True)

    env = environment_record(); env.update(package_version=PACKAGE_VERSION)
    output.with_name("environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    audit = audit_outputs(output, a.algorithms, a.repetitions)
    output.with_name("output_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    maudit = memory_audit(output, memory_output) if memory_output.exists() else {
        "memory_rows": 0, "expected_memory_pairs": 0, "missing_pairs": [],
        "unsuccessful_rows": [], "disagreements": []}
    output.with_name("memory_audit.json").write_text(json.dumps(maudit, indent=2), encoding="utf-8")
    config["finished_utc"] = datetime.now(timezone.utc).isoformat()
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    if audit["incomplete_groups"] or audit["disagreements"] or maudit["missing_pairs"] or maudit["disagreements"]:
        raise SystemExit("incomplete or disagreeing outputs detected; inspect audit JSON files")
    if not a.no_summary:
        cmd = [sys.executable, str(root / "summarize_results.py"), str(output),
               "--manifest", str(manifest_path), "--output-dir", str(output.with_name("summary"))]
        if memory_output.exists(): cmd.extend(["--memory", str(memory_output)])
        subprocess.run(cmd, check=True)


if __name__ == "__main__": main()
