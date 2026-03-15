#!/usr/bin/env python3
"""Simple SQL migration runner for local/dev environments.

Usage:
  python infra/scripts/migrate.py up
  python infra/scripts/migrate.py down --version 0001
  python infra/scripts/migrate.py status

Notes:
- Migration files are discovered from ``infra/migrations`` using the convention
  ``<version>_<name>.up.sql`` and ``<version>_<name>.down.sql``.
- Applied versions are tracked in ``schema_migrations``.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Literal

import psycopg

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "migrations"
Direction = Literal["up", "down"]


def extract_version(file_path: Path) -> str:
    """Return migration version from filename.

    Example:
        ``0001_initial_schema.up.sql`` -> ``0001``
    """
    return file_path.name.split("_")[0]


def migration_files(direction: Direction) -> list[Path]:
    """List migration files ordered for execution.

    ``up`` is applied in ascending order, while ``down`` is evaluated in
    descending order (newest first).
    """
    suffix = f".{direction}.sql"
    files = sorted(MIGRATIONS_DIR.glob(f"*{suffix}"))
    if direction == "down":
        files = list(reversed(files))
    return files


def ensure_table(conn: psycopg.Connection) -> None:
    """Create ``schema_migrations`` table if needed."""
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    conn.commit()


def status(conn: psycopg.Connection) -> None:
    """Print applied migrations in ascending order by version."""
    ensure_table(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT version, applied_at FROM schema_migrations ORDER BY version")
        rows = cur.fetchall()

    if not rows:
        print("No hay migraciones aplicadas.")
        return

    for version, applied_at in rows:
        print(f"{version} | {applied_at.isoformat()}")


def apply_up(conn: psycopg.Connection) -> None:
    """Apply every pending ``.up.sql`` migration file."""
    ensure_table(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        applied = {row[0] for row in cur.fetchall()}

    for path in migration_files("up"):
        version = extract_version(path)
        if version in applied:
            print(f"[skip] {path.name} ya aplicada")
            continue

        sql = path.read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute("INSERT INTO schema_migrations(version) VALUES (%s)", (version,))
        conn.commit()
        print(f"[ok] aplicada {path.name}")


def apply_down(conn: psycopg.Connection, target_version: str | None) -> None:
    """Rollback applied migrations.

    If ``target_version`` is provided, only that specific migration is rolled
    back. Otherwise, all applied migrations are rolled back in reverse order.
    """
    ensure_table(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations ORDER BY version DESC")
        applied = [row[0] for row in cur.fetchall()]

    for path in migration_files("down"):
        version = extract_version(path)
        if version not in applied:
            continue
        if target_version and version != target_version:
            continue

        sql = path.read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))
        conn.commit()
        print(f"[ok] rollback {path.name}")
        if target_version:
            return


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for migration execution."""
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["up", "down", "status"])
    parser.add_argument("--version", default=None, help="Versión específica para rollback (ej: 0001)")
    return parser.parse_args()


def main() -> None:
    """Entrypoint for migration management CLI."""
    args = parse_args()
    db_url = os.getenv("DATABASE_URL", "postgresql://erp_user:erp_pass@127.0.0.1:5432/erp_barrio")

    with psycopg.connect(db_url) as conn:
        if args.action == "status":
            status(conn)
            return
        if args.action == "up":
            apply_up(conn)
            return
        apply_down(conn, args.version)


if __name__ == "__main__":
    main()
