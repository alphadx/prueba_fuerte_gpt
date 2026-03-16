"""Valida presencia de fixtures críticos generados para paso 11."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_FIXTURES = {
    "FX-SALE-CASH",
    "FX-SALE-ELECTRONIC",
    "FX-WEB-PICKUP",
    "FX-BILLING-SBX",
    "FX-PAYMENT-WEBHOOK",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida catálogo de fixtures críticos")
    parser.add_argument("--path", default="infra/seeds/fixtures_state.json", help="Ruta al reporte de fixtures")
    args = parser.parse_args()

    report_path = Path(args.path)
    if not report_path.exists():
        raise SystemExit(f"[fixtures] ERROR: falta {report_path}")

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    fixtures = set(payload.get("fixtures", {}).keys())
    missing = sorted(EXPECTED_FIXTURES - fixtures)
    if missing:
        raise SystemExit(f"[fixtures] ERROR: fixtures faltantes: {missing}")

    print("[fixtures] OK: catálogo crítico completo")


if __name__ == "__main__":
    main()
