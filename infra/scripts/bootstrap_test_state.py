"""Orquestador unificado de bootstrap QA para paso 11.

Ejecuta seed + fixtures + smoke, con resiliencia básica y reporte de tiempos.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_MAX_SECONDS = 600.0
DEFAULT_REPORT_PATH = Path("infra/seeds/bootstrap_report.json")
DEFAULT_STEP_TIMEOUT_SECONDS = 240.0


def _run_step_once(name: str, command: list[str], *, timeout_seconds: float) -> dict[str, Any]:
    start = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()

    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout_seconds)
        timed_out = False
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\n[bootstrap] step timeout after {timeout_seconds}s"

    duration = time.perf_counter() - start

    return {
        "name": name,
        "command": " ".join(command),
        "returncode": returncode,
        "duration_seconds": round(duration, 3),
        "started_at": started_at,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
    }


def _run_step(
    name: str,
    command: list[str],
    *,
    retries: int,
    timeout_seconds: float,
    verbose: bool,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []

    for attempt in range(1, retries + 2):
        if verbose:
            print(f"[bootstrap] step={name} attempt={attempt} command={' '.join(command)}")

        result = _run_step_once(name, command, timeout_seconds=timeout_seconds)
        result["attempt"] = attempt
        attempts.append(result)

        if result["returncode"] == 0:
            if verbose:
                print(f"[bootstrap] step={name} OK in {result['duration_seconds']}s")
            break

        if verbose:
            print(f"[bootstrap] step={name} failed rc={result['returncode']}")

    final = attempts[-1]
    return {
        "name": name,
        "command": " ".join(command),
        "attempts": attempts,
        "returncode": final["returncode"],
        "duration_seconds": round(sum(item["duration_seconds"] for item in attempts), 3),
        "timed_out": any(item["timed_out"] for item in attempts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap QA unificado para paso 11")
    parser.add_argument("--max-seconds", type=float, default=DEFAULT_MAX_SECONDS, help="Tiempo máximo permitido")
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH), help="Ruta de salida del reporte JSON")
    parser.add_argument("--retries", type=int, default=1, help="Reintentos por paso ante fallo")
    parser.add_argument(
        "--step-timeout-seconds",
        type=float,
        default=DEFAULT_STEP_TIMEOUT_SECONDS,
        help="Timeout por paso",
    )
    parser.add_argument("--verbose", action="store_true", help="Imprime avance detallado en consola")
    args = parser.parse_args()

    steps = [
        ("seed", [sys.executable, "infra/scripts/seed.py"]),
        ("seed-validate", [sys.executable, "infra/scripts/validate_seed.py"]),
        ("fixtures", [sys.executable, "infra/scripts/load_fixtures.py"]),
        ("fixtures-validate", [sys.executable, "infra/scripts/validate_fixtures.py"]),
        ("smoke-test-state", [sys.executable, "infra/scripts/smoke_test_state.py"]),
    ]

    started_at = datetime.now(timezone.utc).isoformat()
    start_total = time.perf_counter()
    results: list[dict[str, Any]] = []

    for name, command in steps:
        result = _run_step(
            name,
            command,
            retries=args.retries,
            timeout_seconds=args.step_timeout_seconds,
            verbose=args.verbose,
        )
        results.append(result)
        if result["returncode"] != 0:
            break

    total_seconds = time.perf_counter() - start_total

    report = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "max_seconds": args.max_seconds,
        "step_timeout_seconds": args.step_timeout_seconds,
        "retries": args.retries,
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
