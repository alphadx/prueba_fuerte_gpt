"""Genera el acta de cierre final de salida a partir del consolidado stage 9."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from release_artifacts import load_release_artifact


def _load_payload(path: Path) -> dict[str, object]:
    payload = load_release_artifact(path)
    if "release_validation" not in payload:
        raise SystemExit("[release-closure-acta] ERROR: falta clave release_validation")
    return payload["release_validation"]


def _normalize_gate_status(status: str) -> str:
    mapping = {
        "pass": "PASS",
        "fail": "FAIL",
        "warning_env": "PENDIENTE_ENTORNO",
    }
    return mapping.get(status, status.upper())


def _checklist_item(checked: bool, text: str) -> str:
    return f"- [{'x' if checked else ' '}] {text}"


def _build_blockers(decision: str, risks: list[str], infra_pending: bool) -> list[str]:
    blockers = list(risks)
    if infra_pending and not any("Docker" in risk or "docker" in risk for risk in blockers):
        blockers.append("Infraestructura Docker/Compose pendiente de validación final")
    if not blockers and decision == "GO":
        blockers.append("Sin bloqueos críticos abiertos.")
    return blockers


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera acta de cierre desde release_validation")
    parser.add_argument("--input", default="docs/release_validation_stage9.yaml")
    parser.add_argument("--output", default="docs/release_stage12_closure_acta.md")
    parser.add_argument("--responsable", default=os.getenv("RELEASE_VALIDATION_OWNER", "Release captain"))
    parser.add_argument("--entorno", default=os.getenv("RELEASE_EXECUTION_ENV", socket.gethostname()))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        raise SystemExit(f"[release-closure-acta] ERROR: no existe {input_path}")

    rv = _load_payload(input_path)
    timestamp = rv.get("timestamp_utc", "desconocido")
    commit = rv.get("commit") or subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    decision = str(rv.get("decision", "DESCONOCIDA"))
    observability_file = str(rv.get("observability_snapshot_file", "docs/release_observability_snapshot_stage9.json"))

    gates = rv.get("gates", [])
    gate_map = {item["name"]: item for item in gates if isinstance(item, dict) and "name" in item}
    checklist = rv.get("go_live_checklist", [])
    checklist_map = {item["id"]: item for item in checklist if isinstance(item, dict) and "id" in item}
    critical_risks = [str(item) for item in rv.get("critical_risks_open", [])]
    infra_pending = any(item.get("status") == "warning_env" for item in gates if isinstance(item, dict))

    lines: list[str] = [
        "# Acta de cierre final de salida (Etapa 12)",
        "",
        "> Documento generado automáticamente desde `docs/release_validation_stage9.yaml`.",
        "",
        "## Objetivo",
        "Formalizar el estado de cierre del proceso de salida usando la evidencia consolidada más reciente, incluyendo bloqueos de infraestructura y decisión final vigente.",
        "",
        "## Datos de ejecución",
        f"- Timestamp UTC de evidencia: `{timestamp}`",
        f"- Commit validado: `{commit}`",
        f"- Entorno ejecutor: `{args.entorno}`",
        f"- Responsable de validación: `{args.responsable}`",
        "",
        "## Checklist de cierre",
        _checklist_item(_normalize_gate_status(gate_map.get("make test", {}).get("status", "fail")) == "PASS", "`make test` en PASS."),
        _checklist_item(_normalize_gate_status(gate_map.get("make bootstrap-validate", {}).get("status", "fail")) == "PASS", "`make bootstrap-validate` en PASS."),
        _checklist_item(_normalize_gate_status(gate_map.get("make smoke-test-state", {}).get("status", "fail")) == "PASS", "`make smoke-test-state` en PASS."),
        _checklist_item(checklist_map.get("C4", {}).get("status") == "PASS", "Infraestructura Docker/Compose en PASS (`make doctor-docker` + `make compose-smoke`)."),
        _checklist_item(Path(input_path).exists(), f"`{input_path}` actualizado y versionado."),
        _checklist_item(Path(observability_file).exists(), f"`{observability_file}` actualizado y disponible."),
        "",
        "## Resultado final",
        f"- Decisión vigente: `{decision}`",
        "- Justificación breve:",
    ]

    if decision == "GO":
        lines.extend([
            "  - Todos los gates obligatorios y checks SLO quedaron en PASS.",
            "  - No existen bloqueos críticos abiertos al cierre.",
        ])
    elif decision == "NO-GO":
        lines.extend([
            "  - Se detectaron fallas bloqueantes en gates o SLO críticos.",
            "  - La salida no puede promoverse hasta remediar los hallazgos.",
        ])
    else:
        lines.extend([
            "  - La validación funcional permanece consistente, pero existe bloqueo de entorno para Docker/Compose.",
            "  - El cierre definitivo requiere reejecución en un entorno compatible para convertir el dictamen a `GO` o `NO-GO`.",
        ])

    lines.extend([
        "",
        "## Riesgos críticos y bloqueos al cierre",
    ])

    blockers = _build_blockers(decision, critical_risks, infra_pending)
    for blocker in blockers:
        lines.append(f"- {blocker}")

    lines.extend([
        "",
        "## Estado detallado de checklist consolidado",
    ])
    for item in checklist:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('id', '?')}` → `{item.get('status', 'DESCONOCIDO')}`: {item.get('notes', '')}")

    lines.extend([
        "",
        "## Evidencia adjunta obligatoria",
        f"1. Consolidado de validación: `{input_path}`.",
        f"2. Snapshot de observabilidad: `{observability_file}`.",
        "3. Reporte final del paso: `docs/release_final_report_step12.md`.",
        "4. Handoff operativo para entorno Docker/Compose: `docs/release_env_handoff_stage11.md`.",
        "",
        "## Próximo paso requerido",
    ])

    if decision == "PENDIENTE_ENTORNO":
        lines.append("Ejecutar `make doctor-docker`, `make compose-smoke` y `make release-closure-pipeline-stage9` en un entorno Docker/Compose compatible para cerrar el dictamen final.")
    elif decision == "NO-GO":
        lines.append("Corregir los hallazgos bloqueantes, regenerar la evidencia y volver a emitir esta acta con una nueva corrida de validación.")
    else:
        lines.append("Archivar esta acta como evidencia final de salida aprobada y conservar la trazabilidad de la corrida validada.")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[release-closure-acta] OK: {output_path}")


if __name__ == "__main__":
    main()
