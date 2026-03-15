"""Regression checks for step-4 migration assets.

These tests are static by design (no DB connection required), so they can run
in constrained environments where PostgreSQL/Docker are unavailable.
"""

from pathlib import Path

EXPECTED_TABLES: tuple[str, ...] = (
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
)


def test_initial_migration_contains_all_mvp_tables() -> None:
    """The initial `up` migration must create every MVP table."""
    up_sql = Path("infra/migrations/0001_initial_schema.up.sql").read_text(encoding="utf-8")

    for table in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in up_sql


def test_rollback_drops_all_mvp_tables() -> None:
    """The paired `down` migration must drop every MVP table."""
    down_sql = Path("infra/migrations/0001_initial_schema.down.sql").read_text(encoding="utf-8")

    for table in EXPECTED_TABLES:
        assert f"DROP TABLE IF EXISTS {table};" in down_sql


def test_initial_migration_includes_table_and_column_comments() -> None:
    """The initial migration should document every table and column via COMMENT ON."""
    up_sql = Path("infra/migrations/0001_initial_schema.up.sql").read_text(encoding="utf-8")

    for table in EXPECTED_TABLES:
        assert f"COMMENT ON TABLE {table} IS" in up_sql

    # Column-level documentation for representative critical columns.
    expected_column_comments = (
        "COMMENT ON COLUMN companies.tax_id IS",
        "COMMENT ON COLUMN sales.total IS",
        "COMMENT ON COLUMN online_orders.status IS",
        "COMMENT ON COLUMN employee_documents.expires_on IS",
        "COMMENT ON COLUMN alarm_events.payload IS",
    )
    for marker in expected_column_comments:
        assert marker in up_sql
