"""Valida estructura y criterios mínimos del reporte de bootstrap QA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_STEP_ORDER = [
    "seed",
    "seed-validate",
    "fixtures",
    "fixtures-validate",
    "smoke-test-state",
]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[bootstrap-validate] ERROR: {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida reporte de bootstrap QA")
    parser.add_argument("--path", default="infra/seeds/bootstrap_report.json", help="Ruta al reporte")
    parser.add_argument("--max-seconds", type=float, default=600.0, help="Tiempo máximo esperado")
    args = parser.parse_args()

    report_path = Path(args.path)
    _assert(report_path.exists(), f"no existe reporte: {report_path}")

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    _assert(payload.get("all_steps_passed") is True, "all_steps_passed debe ser true")
    _assert(payload.get("within_target") is True, "within_target debe ser true")
    _assert(float(payload.get("total_seconds", 0.0)) <= args.max_seconds, "runtime total fuera de objetivo")

    steps = payload.get("steps", [])
    names = [step.get("name") for step in steps]
    _assert(names == REQUIRED_STEP_ORDER, f"orden de pasos inválido: {names}")
    _assert(all(step.get("returncode") == 0 for step in steps), "todos los pasos deben retornar 0")

    print("[bootstrap-validate] OK: reporte válido")


if __name__ == "__main__":
    main()
