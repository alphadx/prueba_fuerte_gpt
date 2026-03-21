"""Helpers for reading/writing release artifacts in YAML format."""

from __future__ import annotations

from pathlib import Path

import yaml


def load_release_artifact(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"[release-artifact] ERROR: contenido inválido en {path}")
    return payload


def write_release_artifact(path: Path, payload: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
