"""Validador de invariantes del seed canónico (paso 11)."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


EXPECTED_ROLES = {"admin", "cajero", "bodega", "rrhh"}
EXPECTED_THRESHOLDS = {30, 15, 7, 1}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _load_seed(seed_path: Path) -> dict[str, object]:
    _assert(seed_path.exists(), f"No existe archivo seed: {seed_path}")
    content = seed_path.read_text(encoding="utf-8")
    return json.loads(content)


def validate_seed(seed_data: dict[str, object]) -> list[str]:
    checks: list[str] = []

    company = seed_data.get("company") or {}
    branch = seed_data.get("branch") or {}
    users = seed_data.get("users") or []
    products = seed_data.get("products") or []
    employees = seed_data.get("employees") or []
    documents = seed_data.get("employee_documents") or []
    alarm_rules = seed_data.get("alarm_rules") or []
    meta = seed_data.get("meta") or {}

    _assert(company.get("id") == "comp-001", "company.id debe ser comp-001")
    checks.append("company base OK")

    _assert(branch.get("id") == "branch-001", "branch.id debe ser branch-001")
    _assert(branch.get("company_id") == "comp-001", "branch.company_id debe ser comp-001")
    checks.append("branch base OK")

    roles = {user.get("role") for user in users}
    _assert(EXPECTED_ROLES.issubset(roles), f"roles insuficientes: {roles}")
    checks.append("roles base OK")

    _assert(len(products) == 20, "deben existir 20 productos")
    _assert(all(int(product.get("stock", 0)) > 0 for product in products), "todos los productos deben tener stock > 0")
    checks.append("productos base OK")

    _assert(len(employees) == 2, "deben existir 2 empleados")
    _assert(len(documents) == 2, "deben existir 2 documentos de empleado")
    checks.append("empleados y documentos base OK")

    threshold_values = {int(rule.get("threshold_days", -1)) for rule in alarm_rules if rule.get("is_active") is True}
    _assert(EXPECTED_THRESHOLDS == threshold_values, f"umbrales activos inválidos: {threshold_values}")
    checks.append("reglas de alerta base OK")

    ref_date = dt.date.fromisoformat(str(meta.get("seed_reference_date")))
    expiries = [dt.date.fromisoformat(str(doc["expires_on"])) for doc in documents if "expires_on" in doc]
    _assert(any((expiry - ref_date).days <= 7 for expiry in expiries), "falta documento cercano a vencer <= 7 días")
    checks.append("ventana de vencimiento cercana OK")

    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida invariantes del seed canónico")
    parser.add_argument(
        "--seed-path",
        default="infra/seeds/dev_seed.json",
        help="Ruta al archivo seed JSON",
    )
    args = parser.parse_args()

    seed_path = Path(args.seed_path)
    seed_data = _load_seed(seed_path)
    checks = validate_seed(seed_data)

    for check in checks:
        print(f"[seed-check] {check}")
    print("[seed-check] OK: invariantes cumplidos")


if __name__ == "__main__":
    main()
