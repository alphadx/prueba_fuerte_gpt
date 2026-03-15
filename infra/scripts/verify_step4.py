#!/usr/bin/env python3
"""Validación estática del paso 4 (modelo de datos y migraciones)."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
UP_SQL = ROOT / "infra/migrations/0001_initial_schema.up.sql"
DOWN_SQL = ROOT / "infra/migrations/0001_initial_schema.down.sql"
ER_DOC = ROOT / "infra/migrations/README.md"

EXPECTED_TABLES = [
    "companies",
    "branches",
    "users",
    "roles",
    "products",
    "stock_items",
    "stock_movements",
    "sales",
    "sale_lines",
    "payments",
    "cash_sessions",
    "tax_documents",
    "tax_document_events",
    "online_orders",
    "pickup_slots",
    "employees",
    "document_types",
    "employee_documents",
    "alarm_rules",
    "alarm_events",
]

EXPECTED_JSONB_COLUMNS = [
    "custom_data JSONB",
    "schema_definition JSONB",
    "metadata JSONB",
    "payload JSONB",
]


def assert_contains(content: str, needle: str, label: str) -> None:
    if needle not in content:
        raise AssertionError(f"Falta {label}: {needle}")


def main() -> int:
    up_sql = UP_SQL.read_text(encoding="utf-8")
    down_sql = DOWN_SQL.read_text(encoding="utf-8")
    er_doc = ER_DOC.read_text(encoding="utf-8")

    for table in EXPECTED_TABLES:
        assert_contains(up_sql, f"CREATE TABLE IF NOT EXISTS {table}", "tabla en migración up")
        assert_contains(down_sql, f"DROP TABLE IF EXISTS {table};", "tabla en migración down")

    for column in EXPECTED_JSONB_COLUMNS:
        assert_contains(up_sql, column, "columna JSONB requerida")

    assert_contains(up_sql, "CREATE INDEX IF NOT EXISTS idx_sales_branch_sold_at", "índice de ventas")
    assert_contains(up_sql, "CREATE INDEX IF NOT EXISTS idx_alarm_events_status_triggered", "índice de alarmas")
    assert_contains(er_doc, "```mermaid", "diagrama ER")

    print("[ok] Validación estática del paso 4 completada")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"[error] {exc}")
        raise SystemExit(1)
