"""Evalúa estabilidad de bootstrap ejecutándolo múltiples veces."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecuta bootstrap repetidas veces y calcula estabilidad")
    parser.add_argument("--runs", type=int, default=5, help="Cantidad de corridas")
    parser.add_argument("--min-success-rate", type=float, default=95.0, help="Umbral mínimo de éxito (%)")
    parser.add_argument("--max-seconds", type=float, default=600.0)
    parser.add_argument("--output", default="infra/seeds/bootstrap_stability.json")
    args = parser.parse_args()

    results = []
    successes = 0

    for idx in range(1, args.runs + 1):
        report_path = Path(f"infra/seeds/bootstrap_report_run_{idx:02d}.json")
        cmd = [
            sys.executable,
            "infra/scripts/bootstrap_test_state.py",
            "--max-seconds",
            str(args.max_seconds),
            "--report-path",
            str(report_path),
        ]
        run = subprocess.run(cmd, check=False, capture_output=True, text=True)
        ok = run.returncode == 0
        if ok:
            successes += 1
        results.append(
            {
                "run": idx,
                "returncode": run.returncode,
                "ok": ok,
                "report_path": str(report_path),
            }
        )

    success_rate = (successes / args.runs) * 100.0
    summary = {
        "runs": args.runs,
        "successes": successes,
        "success_rate": round(success_rate, 2),
        "min_success_rate": args.min_success_rate,
        "passes_threshold": success_rate >= args.min_success_rate,
        "results": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not summary["passes_threshold"]:
        raise SystemExit(
            f"[bootstrap-stability] ERROR: success_rate={success_rate:.2f}% < min={args.min_success_rate:.2f}%"
        )

    print(f"[bootstrap-stability] OK: success_rate={success_rate:.2f}%")


if __name__ == "__main__":
    main()
