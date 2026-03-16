import json
import subprocess
from pathlib import Path


def test_seed_pipeline_generates_canonical_dataset(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed.json"

    run_seed = subprocess.run(
        [
            "python3",
            "infra/scripts/seed.py",
            "--reference-date",
            "2025-01-15",
            "--output",
            str(seed_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run_seed.returncode == 0, run_seed.stderr
    assert seed_path.exists()

    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    assert payload["company"]["id"] == "comp-001"
    assert len(payload["products"]) == 20
    assert {item["role"] for item in payload["users"]} >= {"admin", "cajero", "bodega", "rrhh"}

    run_validate = subprocess.run(
        ["python3", "infra/scripts/validate_seed.py", "--seed-path", str(seed_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert run_validate.returncode == 0, run_validate.stderr
    assert "[seed-check] OK: invariantes cumplidos" in run_validate.stdout
