"""Smoke checks de estado QA para paso 11.

Valida que el estado generado por seed+fixtures sea ejecutable para QA.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"[smoke] ERROR: no existe {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"[smoke] ERROR: {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke checks para estado QA de bootstrap")
    parser.add_argument("--seed-path", default="infra/seeds/dev_seed.json")
    parser.add_argument("--fixtures-path", default="infra/seeds/fixtures_state.json")
    args = parser.parse_args()

    seed = _load_json(Path(args.seed_path))
    fixtures = _load_json(Path(args.fixtures_path)).get("fixtures", {})

    _assert(len(seed.get("products", [])) == 20, "seed debe contener 20 productos")
    _assert(len(seed.get("users", [])) >= 4, "seed debe contener usuarios por rol")

    required = {
        "FX-SALE-CASH",
        "FX-SALE-ELECTRONIC",
        "FX-WEB-PICKUP",
        "FX-BILLING-SBX",
        "FX-PAYMENT-WEBHOOK",
    }
    _assert(required.issubset(set(fixtures.keys())), "faltan fixtures críticos")

    _assert(fixtures["FX-SALE-CASH"].get("status") == "paid", "FX-SALE-CASH debe quedar paid")
    _assert(fixtures["FX-SALE-ELECTRONIC"].get("status") == "confirmed", "FX-SALE-ELECTRONIC debe quedar confirmed")
    _assert(fixtures["FX-WEB-PICKUP"].get("state") == "recibido", "FX-WEB-PICKUP debe quedar recibido")
    _assert(
        fixtures["FX-BILLING-SBX"].get("document_status") in {"accepted", "queued"},
        "FX-BILLING-SBX debe quedar accepted/queued",
    )
    _assert(fixtures["FX-PAYMENT-WEBHOOK"].get("duplicated") is True, "FX-PAYMENT-WEBHOOK debe detectar duplicado")

    print("[smoke] OK: estado QA ejecutable")


if __name__ == "__main__":
    main()
