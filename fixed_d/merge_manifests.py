"""Merge preregistered study blocks without changing any instance."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("manifests", nargs="+"); p.add_argument("--output", required=True)
    a = p.parse_args(); records = []; sources = []
    for name in a.manifests:
        path = Path(name).resolve(); data = json.loads(path.read_text(encoding="utf-8"))
        records.extend(data["instances"]); sources.append(str(path))
    keys = [str(Path(r["path"]).resolve()) for r in records]
    if len(keys) != len(set(keys)): raise SystemExit("duplicate instance path across manifests")
    out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"schema": 2, "study": "combined fixed-d final corpus",
                               "source_manifests": sources, "instances": records}, indent=2), encoding="utf-8")
    print(f"wrote {len(records)} cases to {out}")


if __name__ == "__main__": main()
