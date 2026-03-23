"""Valida consistencia del consolidado de release_validation stage 9."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from release_artifacts import load_release_artifact


GATE_TO_CHECK_ID = {
    "make test": "C1",
    "make bootstrap-validate": "C2",
    "make smoke-test-state": "C3",
    "make doctor-docker && make compose-smoke": "C4",
}
SLO_TO_CHECK_ID = {
    "billing.error_rate <= 2.0": "C5",
    "payments.error_rate <= 3.0": "C6",
    "api health/readiness": "C7",
}
STATUS_MAP = {
    "pass": "PASS",
    "fail": "FAIL",
    "warning_env": "PENDIENTE_ENTORNO",
}
BLOCKING_CHECKS = {"C1", "C2", "C3", "C4", "C5", "C6", "C7"}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[release-validate] ERROR: {message}")


def _expected_decision(*, gates: list[dict[str, object]], slo_checks: list[dict[str, object]]) -> str:
    has_gate_fail = any(item.get("status") == "fail" for item in gates)
    has_warning_env = any(item.get("status") == "warning_env" for item in gates)
    has_slo_fail = any(item.get("status") == "fail" for item in slo_checks)

    if has_gate_fail or has_slo_fail:
        return "NO-GO"
    if has_warning_env:
        return "PENDIENTE_ENTORNO"
    return "GO"


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida consistencia de release_validation")
    parser.add_argument("--path", default="docs/release_validation_stage9.yaml")
    args = parser.parse_args()

    path = Path(args.path)
    _assert(path.exists(), f"no existe {path}")

    payload = load_release_artifact(path)
    _assert("release_validation" in payload, "falta clave release_validation")
    rv = payload["release_validation"]

    required = [
        "timestamp_utc",
        "commit",
        "gates",
        "slo_checks",
        "go_live_checklist",
        "observability_snapshot_file",
        "decision",
        "critical_risks_open",
    ]
    for key in required:
        _assert(key in rv, f"falta campo {key}")

    gates = rv["gates"]
    _assert(isinstance(gates, list) and len(gates) >= 4, "gates inválido")
    gate_by_name = {item["name"]: item for item in gates if isinstance(item, dict) and "name" in item}
    for gate_name in GATE_TO_CHECK_ID:
        _assert(gate_name in gate_by_name, f"falta gate {gate_name}")

    slo_checks = rv["slo_checks"]
    _assert(isinstance(slo_checks, list) and len(slo_checks) >= 3, "slo_checks inválido")
    slo_by_name = {item["name"]: item for item in slo_checks if isinstance(item, dict) and "name" in item}
    for slo_name in SLO_TO_CHECK_ID:
        _assert(slo_name in slo_by_name, f"falta SLO {slo_name}")

    checklist = rv["go_live_checklist"]
    _assert(isinstance(checklist, list) and len(checklist) >= 10, "go_live_checklist inválido")
    checklist_by_id = {item["id"]: item for item in checklist if isinstance(item, dict) and "id" in item}
    for check_id in [*GATE_TO_CHECK_ID.values(), *SLO_TO_CHECK_ID.values(), "C8", "C9", "C10"]:
        _assert(check_id in checklist_by_id, f"falta checklist {check_id}")

    snapshot_path = Path(rv["observability_snapshot_file"])
    _assert(snapshot_path.exists(), f"no existe snapshot {snapshot_path}")

    for gate_name, check_id in GATE_TO_CHECK_ID.items():
        expected = STATUS_MAP[gate_by_name[gate_name]["status"]]
        actual = checklist_by_id[check_id]["status"]
        _assert(actual == expected, f"checklist {check_id} inconsistente con gate {gate_name}: actual={actual}, esperado={expected}")

    for slo_name, check_id in SLO_TO_CHECK_ID.items():
        expected = STATUS_MAP[slo_by_name[slo_name]["status"]]
        actual = checklist_by_id[check_id]["status"]
        _assert(actual == expected, f"checklist {check_id} inconsistente con SLO {slo_name}: actual={actual}, esperado={expected}")

    actual_decision = rv["decision"]
    expected_decision = _expected_decision(gates=gates, slo_checks=slo_checks)
    _assert(actual_decision == expected_decision, f"decision inconsistente: actual={actual_decision}, esperado={expected_decision}")

    blocking_statuses = {check_id: checklist_by_id[check_id]["status"] for check_id in BLOCKING_CHECKS}
    if actual_decision == "NO-GO":
        _assert(any(status == "FAIL" for status in blocking_statuses.values()), "NO-GO requiere al menos un check bloqueante en FAIL")
    elif actual_decision == "PENDIENTE_ENTORNO":
        _assert(any(status == "PENDIENTE_ENTORNO" for status in blocking_statuses.values()), "PENDIENTE_ENTORNO requiere al menos un check bloqueante pendiente de entorno")
        _assert(not any(status == "FAIL" for status in blocking_statuses.values()), "PENDIENTE_ENTORNO no puede coexistir con checks bloqueantes en FAIL")
    else:
        _assert(all(status == "PASS" for status in blocking_statuses.values()), "GO requiere todos los checks bloqueantes en PASS")

    risks = rv["critical_risks_open"]
    _assert(isinstance(risks, list), "critical_risks_open inválido")
    if any(item.get("status") == "warning_env" for item in gates):
        _assert(any("Docker" in str(risk) or "docker" in str(risk) for risk in risks), "warning_env requiere riesgo crítico asociado a Docker/Compose")
    if slo_by_name["billing.error_rate <= 2.0"]["status"] == "fail":
        _assert(any("billing.error_rate" in str(risk) for risk in risks), "billing SLO en FAIL requiere riesgo crítico asociado")
    if slo_by_name["payments.error_rate <= 3.0"]["status"] == "fail":
        _assert(any("payments.error_rate" in str(risk) for risk in risks), "payments SLO en FAIL requiere riesgo crítico asociado")

    print(f"[release-validate] OK: {path} consistente (decision={actual_decision})")


if __name__ == "__main__":
    main()
