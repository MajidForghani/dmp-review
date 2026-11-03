"""Fast integrity checks for the public reproducibility archive."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as stream:
        return sum(1 for _ in csv.DictReader(stream))


def check_study(
    directory: str,
    manifest_rel: str,
    results_rel: str,
    expected_instances: int,
    expected_timing_rows: int,
    expected_memory_rows: int,
) -> None:
    base = ROOT / directory
    manifest_path = base / manifest_rel
    manifest = read_json(manifest_path)
    assert len(manifest["instances"]) == expected_instances

    missing = [item["path"] for item in manifest["instances"] if not (base / item["path"]).is_file()]
    assert not missing, f"missing instance files: {missing[:3]}"

    results = base / results_rel
    assert row_count(results / "timing_raw.csv") == expected_timing_rows
    assert row_count(results / "timing_raw_memory.csv") == expected_memory_rows

    config = read_json(results / "run_config.json")
    public_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    assert config["manifest_sha256"] == public_hash

    checks = read_json(results / "summary" / "analysis_checks.json")
    assert checks["timing_rows"] == expected_timing_rows
    assert checks["cases"] == expected_instances
    assert checks["inconsistent_repetition_digests"] == 0
    assert checks["fully_unsolved_cases"] == 0


def main() -> None:
    check_study(
        "fixed_d",
        "study/fixed_d_complete/manifest.json",
        "results/fixed_d_final",
        expected_instances=94,
        expected_timing_rows=1410,
        expected_memory_rows=470,
    )
    check_study(
        "all_demand",
        "study/all_demand_final/manifest.json",
        "results/all_demand_final",
        expected_instances=37,
        expected_timing_rows=444,
        expected_memory_rows=148,
    )
    print("release integrity checks passed")


if __name__ == "__main__":
    main()

