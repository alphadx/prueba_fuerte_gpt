from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "infra" / "scripts" / "generate_release_evidence.py"
SPEC = importlib.util.spec_from_file_location("release_evidence", SCRIPT_PATH)
assert SPEC and SPEC.loader
release_evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_evidence)
ARTIFACTS_PATH = ROOT / "infra" / "scripts" / "release_artifacts.py"
ARTIFACTS_SPEC = importlib.util.spec_from_file_location("release_artifacts", ARTIFACTS_PATH)
assert ARTIFACTS_SPEC and ARTIFACTS_SPEC.loader
release_artifacts = importlib.util.module_from_spec(ARTIFACTS_SPEC)
ARTIFACTS_SPEC.loader.exec_module(release_artifacts)


@pytest.mark.parametrize(
    ("gate_status", "billing_error", "payments_error", "expected"),
    [
        ([{"status": "pass"}], 0.0, 0.0, "GO"),
        ([{"status": "warning_env"}], 0.0, 0.0, "PENDIENTE_ENTORNO"),
        ([{"status": "fail"}], 0.0, 0.0, "NO-GO"),
        ([{"status": "pass"}], 2.5, 0.0, "NO-GO"),
        ([{"status": "pass"}], 0.0, 3.5, "NO-GO"),
    ],
)
def test_release_decision_for_expected_status(gate_status, billing_error, payments_error, expected) -> None:
    assert (
        release_evidence._decision_for(
            gate_results=gate_status,
            billing_error=billing_error,
            payments_error=payments_error,
        )
        == expected
    )


def test_release_run_gate_executes_compose_after_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str]) -> tuple[str, str]:
        calls.append(command)
        return "pass", "ok"

    monkeypatch.setattr(release_evidence, "_run_command", fake_run)

    status, notes = release_evidence._run_gate(
        release_evidence.DOCKER_GATE_NAME,
        [["make", "doctor-docker"], ["make", "compose-smoke"]],
    )

    assert status == "pass"
    assert calls == [["make", "doctor-docker"], ["make", "compose-smoke"]]
    assert "compose-smoke: ok" in notes


def test_release_run_gate_stops_on_warning_env(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str]) -> tuple[str, str]:
        calls.append(command)
        if command == ["make", "doctor-docker"]:
            return "warning_env", "Docker/Compose no disponible en entorno actual"
        return "pass", "ok"

    monkeypatch.setattr(release_evidence, "_run_command", fake_run)

    status, notes = release_evidence._run_gate(
        release_evidence.DOCKER_GATE_NAME,
        [["make", "doctor-docker"], ["make", "compose-smoke"]],
    )

    assert status == "warning_env"
    assert notes == "Docker/Compose no disponible en entorno actual"
    assert calls == [["make", "doctor-docker"]]


def test_validate_release_evidence_rejects_inconsistent_checklist(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text("{}", encoding="utf-8")
    evidence = tmp_path / "release_validation_stage9.yaml"
    release_artifacts.write_release_artifact(
        evidence,
        {
            "release_validation": {
                "timestamp_utc": "2026-03-21T00:00:00Z",
                "commit": "deadbee",
                "gates": [
                    {"name": "make test", "status": "pass", "notes": "ok"},
                    {"name": "make bootstrap-validate", "status": "pass", "notes": "ok"},
                    {"name": "make smoke-test-state", "status": "pass", "notes": "ok"},
                    {
                        "name": release_evidence.DOCKER_GATE_NAME,
                        "status": "warning_env",
                        "notes": "Docker/Compose no disponible en entorno actual",
                    },
                ],
                "observability_snapshot_file": str(snapshot),
                "slo_checks": [
                    {"name": "billing.error_rate <= 2.0", "observed": 0.0, "status": "pass"},
                    {"name": "payments.error_rate <= 3.0", "observed": 0.0, "status": "pass"},
                    {"name": "api health/readiness", "observed": "ok/ready", "status": "pass"},
                ],
                "go_live_checklist": [
                    {"id": "C1", "status": "PASS", "notes": "suite principal"},
                    {"id": "C2", "status": "PASS", "notes": "bootstrap report"},
                    {"id": "C3", "status": "PASS", "notes": "smoke estado QA"},
                    {"id": "C4", "status": "PASS", "notes": "inconsistente"},
                    {"id": "C5", "status": "PASS", "notes": "billing.error_rate <= 2.0"},
                    {"id": "C6", "status": "PASS", "notes": "payments.error_rate <= 3.0"},
                    {"id": "C7", "status": "PASS", "notes": "health/readiness"},
                    {"id": "C8", "status": "PASS", "notes": "runbooks y owners"},
                    {"id": "C9", "status": "PASS", "notes": "evidencia versionada"},
                    {"id": "C10", "status": "PASS", "notes": "sin secretos en diff"},
                ],
                "decision": "PENDIENTE_ENTORNO",
                "critical_risks_open": ["No disponibilidad de Docker en entorno validación"],
            }
        },
    )

    result = subprocess.run(
        [sys.executable, "infra/scripts/validate_release_evidence.py", "--path", str(evidence)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    assert result.returncode != 0
    assert "checklist C4 inconsistente" in result.stderr or "checklist C4 inconsistente" in result.stdout


def test_release_artifact_helper_writes_yaml(tmp_path: Path) -> None:
    path = tmp_path / "artifact.yaml"
    release_artifacts.write_release_artifact(path, {"release_validation": {"decision": "GO"}})

    body = path.read_text(encoding="utf-8")
    assert not body.lstrip().startswith("{")
    assert yaml.safe_load(body)["release_validation"]["decision"] == "GO"
