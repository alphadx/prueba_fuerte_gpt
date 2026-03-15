#!/usr/bin/env python3
"""Simple SQL migration runner for local/dev environments.

Usage:
  python infra/scripts/migrate.py up
  python infra/scripts/migrate.py down --version 0001
  python infra/scripts/migrate.py status
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "migrations"


def migration_files(direction: str) -> list[Path]:
    suffix = f".{direction}.sql"
    files = sorted(MIGRATIONS_DIR.glob(f"*{suffix}"))
    if direction == "down":
        files = list(reversed(files))
    return files


def ensure_table(conn: psycopg.Connection) -> None:
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
    ensure_table(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        applied = {row[0] for row in cur.fetchall()}

    for path in migration_files("up"):
        version = path.name.split("_")[0]
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
    ensure_table(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations ORDER BY version DESC")
        applied = [row[0] for row in cur.fetchall()]

    for path in migration_files("down"):
        version = path.name.split("_")[0]
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
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["up", "down", "status"])
    parser.add_argument("--version", default=None, help="Versión específica para rollback (ej: 0001)")
    return parser.parse_args()


def main() -> None:
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
