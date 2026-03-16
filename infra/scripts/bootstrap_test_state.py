"""Orquestador unificado de bootstrap QA para paso 11.

Ejecuta seed + fixtures + smoke y reporta tiempos por etapa.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

DEFAULT_MAX_SECONDS = 600.0
DEFAULT_REPORT_PATH = Path("infra/seeds/bootstrap_report.json")


def _run_step(name: str, command: list[str]) -> dict[str, Any]:
    start = time.perf_counter()
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    duration = time.perf_counter() - start

    return {
        "name": name,
        "command": " ".join(command),
        "returncode": completed.returncode,
        "duration_seconds": round(duration, 3),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap QA unificado para paso 11")
    parser.add_argument("--max-seconds", type=float, default=DEFAULT_MAX_SECONDS, help="Tiempo máximo permitido")
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH), help="Ruta de salida del reporte JSON")
    args = parser.parse_args()

    steps = [
        ("seed", [sys.executable, "infra/scripts/seed.py"]),
        ("seed-validate", [sys.executable, "infra/scripts/validate_seed.py"]),
        ("fixtures", [sys.executable, "infra/scripts/load_fixtures.py"]),
        ("fixtures-validate", [sys.executable, "infra/scripts/validate_fixtures.py"]),
        ("smoke-test-state", [sys.executable, "infra/scripts/smoke_test_state.py"]),
    ]

    start_total = time.perf_counter()
    results: list[dict[str, Any]] = []

    for name, command in steps:
        result = _run_step(name, command)
        results.append(result)
        if result["returncode"] != 0:
            break

    total_seconds = time.perf_counter() - start_total

    report = {
        "max_seconds": args.max_seconds,
        "total_seconds": round(total_seconds, 3),
        "within_target": total_seconds <= args.max_seconds,
        "all_steps_passed": all(step["returncode"] == 0 for step in results) and len(results) == len(steps),
        "steps": results,
    }

    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not report["all_steps_passed"]:
        print(f"[bootstrap] ERROR: alguna etapa falló. Ver reporte en {report_path}")
        raise SystemExit(1)

    if not report["within_target"]:
        print(f"[bootstrap] ERROR: runtime excede objetivo ({total_seconds:.2f}s > {args.max_seconds:.2f}s)")
        raise SystemExit(1)

    print(f"[bootstrap] OK: estado QA listo en {total_seconds:.2f}s (objetivo <= {args.max_seconds:.2f}s)")
    print(f"[bootstrap] Reporte: {report_path}")


if __name__ == "__main__":
    main()
