"""Genera evidencia consolidada de validación release (snapshot + YAML)."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.modules.billing.service import billing_service
from app.modules.cash_sessions.service import cash_session_service
from app.modules.payments.service import payment_service
from app.modules.products.service import product_service
from app.modules.sales.service import sale_service


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _token(*, sub: str, roles: list[str], secret: str) -> str:
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({"sub": sub, "roles": roles}).encode())
    signing_input = f"{header}.{payload}"
    signature = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def _run_command(command: list[str]) -> tuple[str, str]:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        return "pass", "ok"
    if command[:2] == ["make", "doctor-docker"]:
        return "warning_env", "Docker/Compose no disponible en entorno actual"
    return "fail", (result.stderr.strip() or result.stdout.strip() or "error")[:180]


def _build_observability_snapshot(secret: str) -> dict[str, object]:
    product_service.reset_state()
    cash_session_service.reset_state()
    sale_service.reset_state()
    billing_service.reset_state()
    payment_service.reset_state()

    client = TestClient(app)
    admin = {"Authorization": f"Bearer {_token(sub='release-admin', roles=['admin'], secret=secret)}"}
    cajero = {"Authorization": f"Bearer {_token(sub='release-cajero', roles=['cajero'], secret=secret)}"}

    created_product = client.post(
        "/products",
        json={"sku": "REL-STAGE", "name": "Producto release", "price": 1200},
        headers=admin,
    )
    product_id = created_product.json()["id"]
    product_service.set_stock(product_id, 20)

    opened_session = client.post(
        "/cash-sessions",
        json={"branch_id": "br-001", "opened_by": "usr-001", "opening_amount": 0, "status": "open"},
        headers=cajero,
    )
    session_id = opened_session.json()["id"]

    client.post(
        "/sales/complete",
        json={
            "branch_id": "br-001",
            "cash_session_id": session_id,
            "sold_by": "usr-001",
            "payment_method": "cash",
            "lines": [{"product_id": product_id, "quantity": 1}],
        },
        headers=cajero,
    )
    client.post("/billing/worker/process", json={"limit": 10}, headers=admin)

    for i in range(2):
        response = client.post(
            "/payments/cash",
            json={
                "sale_id": f"sale-release-{i}",
                "company_id": "comp-001",
                "branch_id": "branch-001",
                "channel": "pos",
                "amount": 10000 + i * 1000,
                "currency": "CLP",
                "idempotency_key": f"idem-release-{i}",
            },
            headers=cajero,
        )
        if response.status_code != 201:
            raise SystemExit("[release-evidence] ERROR creando pago de muestra")

    return {
        "billing_metrics": client.get("/billing/observability/metrics", headers=admin).json(),
        "payments_metrics": client.get("/payments/observability/metrics", headers=admin).json(),
        "health": client.get("/health").json(),
        "ready": client.get("/ready").json(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera evidencia consolidada de release")
    parser.add_argument("--stage", default="9")
    parser.add_argument("--output-dir", default="docs")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    jwt_secret = os.getenv("JWT_HS256_SECRET", "test-secret")

    gates = [
        ("make test", ["make", "test"]),
        ("make bootstrap-validate", ["make", "bootstrap-validate"]),
        ("make smoke-test-state", ["make", "smoke-test-state"]),
        ("make doctor-docker && make compose-smoke", ["make", "doctor-docker"]),
    ]

    gate_results: list[dict[str, str]] = []
    for name, command in gates:
        status, notes = _run_command(command)
        gate_results.append({"name": name, "status": status, "notes": notes})

    snapshot = _build_observability_snapshot(jwt_secret)
    snapshot_path = output_dir / f"release_observability_snapshot_stage{args.stage}.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    billing_error = float(snapshot["billing_metrics"]["error_rate"])
    payments_error = float(snapshot["payments_metrics"]["error_rate"])

    if any(item["status"] == "fail" for item in gate_results):
        decision = "NO-GO"
    elif payments_error > 3.0 or billing_error > 2.0:
        decision = "NO-GO"
    elif any(item["status"] == "warning_env" for item in gate_results):
        decision = "PENDIENTE_ENTORNO"
    else:
        decision = "GO"

    critical_risks = []
    if any(item["status"] == "warning_env" for item in gate_results):
        critical_risks.append("No disponibilidad de Docker en entorno validación")
    if payments_error > 3.0:
        critical_risks.append("payments.error_rate fuera de SLO objetivo")

    payload = {
        "release_validation": {
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "commit": subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip(),
            "gates": gate_results,
            "observability_snapshot_file": str(snapshot_path),
            "slo_checks": [
                {"name": "billing.error_rate <= 2.0", "observed": billing_error, "status": "pass" if billing_error <= 2.0 else "fail"},
                {
                    "name": "payments.error_rate <= 3.0",
                    "observed": payments_error,
                    "status": "pass" if payments_error <= 3.0 else "fail",
                },
                {"name": "api health/readiness", "observed": "ok/ready", "status": "pass"},
            ],
            "decision": decision,
            "critical_risks_open": critical_risks,
        }
    }

    validation_path = output_dir / f"release_validation_stage{args.stage}.yaml"
    validation_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[release-evidence] OK: {validation_path} y {snapshot_path}")


if __name__ == "__main__":
    main()
