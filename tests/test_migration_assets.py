from pathlib import Path


def test_initial_migration_contains_all_mvp_tables() -> None:
    up_sql = Path("infra/migrations/0001_initial_schema.up.sql").read_text(encoding="utf-8")
    expected_tables = [
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

    for table in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in up_sql


def test_rollback_drops_all_mvp_tables() -> None:
    down_sql = Path("infra/migrations/0001_initial_schema.down.sql").read_text(encoding="utf-8")
    expected_drops = [
        "alarm_events",
        "alarm_rules",
        "employee_documents",
        "document_types",
        "employees",
        "online_orders",
        "pickup_slots",
        "tax_document_events",
        "tax_documents",
        "payments",
        "sale_lines",
        "sales",
        "cash_sessions",
        "stock_movements",
        "stock_items",
        "products",
        "users",
        "roles",
        "branches",
        "companies",
    ]

    for table in expected_drops:
        assert f"DROP TABLE IF EXISTS {table};" in down_sql
