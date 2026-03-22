"""Generador de seed canónico para paso 11.

Este script produce un dataset determinístico en `infra/seeds/dev_seed.json`.
La salida está diseñada para ser idempotente entre ejecuciones.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

DEFAULT_REFERENCE_DATE = "2025-01-15"
DEFAULT_OUTPUT_PATH = Path("infra/seeds/dev_seed.json")


def _build_users() -> list[dict[str, str]]:
    return [
        {"id": "usr-admin-001", "email": "admin@example.com", "role": "admin"},
        {"id": "usr-cajero-001", "email": "cajero@example.com", "role": "cajero"},
        {"id": "usr-bodega-001", "email": "bodega@example.com", "role": "bodega"},
        {"id": "usr-rrhh-001", "email": "rrhh@example.com", "role": "rrhh"},
    ]


def _build_products() -> list[dict[str, object]]:
    products: list[dict[str, object]] = []
    for idx in range(1, 21):
        products.append(
            {
                "id": f"prod-{idx:03d}",
                "sku": f"SKU-{idx:03d}",
                "name": f"Producto Semilla {idx:02d}",
                "price": 1000 + idx * 100,
                "stock": 15 + idx,
            }
        )
    return products


def _build_seed(reference_date: dt.date) -> dict[str, object]:
    near_expiry = reference_date + dt.timedelta(days=7)
    healthy_expiry = reference_date + dt.timedelta(days=90)

    return {
        "meta": {
            "seed_version": "step11-v1",
            "seed_reference_date": reference_date.isoformat(),
            "generated_at": reference_date.isoformat(),
            "deterministic": True,
        },
        "company": {
            "id": "comp-001",
            "name": "Demo ERP Barrio",
            "rut": "76.123.456-7",
        },
        "branch": {
            "id": "branch-001",
            "company_id": "comp-001",
            "name": "Casa Matriz",
            "code": "BR-001",
        },
        "users": _build_users(),
        "products": _build_products(),
        "employees": [
            {"id": "emp-001", "rut": "12.345.678-5", "full_name": "Ana Pérez"},
            {"id": "emp-002", "rut": "10.111.222-3", "full_name": "Juan Soto"},
        ],
        "document_types": [
            {
                "code": "CONTRATO",
                "name": "Contrato de trabajo",
                "requires_expiry": True,
                "schema_version": 1,
            }
        ],
        "employee_documents": [
            {
                "id": "edoc-001",
                "employee_id": "emp-001",
                "document_type_code": "CONTRATO",
                "issue_on": reference_date.isoformat(),
                "expires_on": near_expiry.isoformat(),
                "status": "vigente",
            },
            {
                "id": "edoc-002",
                "employee_id": "emp-002",
                "document_type_code": "CONTRATO",
                "issue_on": reference_date.isoformat(),
                "expires_on": healthy_expiry.isoformat(),
                "status": "vigente",
            },
        ],
        "alarm_rules": [
            {"id": "arule-030", "threshold_days": 30, "is_active": True},
            {"id": "arule-015", "threshold_days": 15, "is_active": True},
            {"id": "arule-007", "threshold_days": 7, "is_active": True},
            {"id": "arule-001", "threshold_days": 1, "is_active": True},
        ],
        "fixtures_catalog": [
            {"id": "FX-SALE-CASH", "scenario": "cash_sale"},
            {"id": "FX-SALE-ELECTRONIC", "scenario": "electronic_sale"},
            {"id": "FX-WEB-PICKUP", "scenario": "web_pickup_order"},
            {"id": "FX-BILLING-SBX", "scenario": "billing_sandbox"},
            {"id": "FX-PAYMENT-WEBHOOK", "scenario": "payment_webhook"},
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el seed canónico para paso 11")
    parser.add_argument(
        "--reference-date",
        default=DEFAULT_REFERENCE_DATE,
        help="Fecha de referencia ISO (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Ruta de salida del JSON de seed",
    )
    args = parser.parse_args()

    reference_date = dt.date.fromisoformat(args.reference_date)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    seed_data = _build_seed(reference_date)
    payload = json.dumps(seed_data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    output_path.write_text(payload, encoding="utf-8")

    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    print(f"Seed canónico generado en {output_path}")
    print(f"SHA256={digest}")


if __name__ == "__main__":
    main()
